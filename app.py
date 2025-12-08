"""
Minute Mail Web Application with Supabase Authentication
Upload mail photos, scan for sender information, and export to spreadsheet
"""

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from minute_mail import MinuteMail
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from io import BytesIO
import gc

# Import Supabase helpers
from supabase_client import (
    get_current_user,
    require_auth,
    sign_up,
    sign_in,
    sign_out,
    create_scan_result,
    get_user_scan_results,
    delete_scan_result,
    clear_user_scan_results,
    get_user_subscription,
    create_user_subscription,
    update_user_subscription,
    increment_scan_count,
    can_user_scan
)

# Import Stripe helpers
from stripe_client import (
    create_customer,
    create_checkout_session,
    get_subscription,
    cancel_subscription,
    update_subscription,
    construct_webhook_event,
    get_plan_info,
    get_all_plans,
    create_customer_portal_session,
    STRIPE_PUBLISHABLE_KEY
)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max total upload size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['EXPORT_FOLDER'] = 'exports'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic', 'heif'}

# Create necessary folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)

# Initialize Minute Mail
scanner = MinuteMail()


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Authentication Routes

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler"""
    if request.method == 'GET':
        # If already logged in, redirect to main app
        if get_current_user():
            return redirect(url_for('index'))
        return render_template('login.html')

    # Handle login POST
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return render_template('login.html', error='Please provide both email and password')

    success, data = sign_in(email, password)

    if success:
        # Store access token and refresh token in session
        session['access_token'] = data['access_token']
        session['refresh_token'] = data['session'].refresh_token if data.get('session') else None
        session['user_id'] = str(data['user'].id)
        return redirect(url_for('index'))
    else:
        error_msg = data.get('error', 'Invalid email or password')
        return render_template('login.html', error=error_msg)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page and handler"""
    if request.method == 'GET':
        # If already logged in, redirect to main app
        if get_current_user():
            return redirect(url_for('index'))
        return render_template('signup.html')

    # Handle signup POST
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if not email or not password:
        return render_template('signup.html', error='Please provide both email and password')

    if password != confirm_password:
        return render_template('signup.html', error='Passwords do not match')

    if len(password) < 6:
        return render_template('signup.html', error='Password must be at least 6 characters')

    success, data = sign_up(email, password)

    if success:
        # Auto-login after successful signup
        if data.get('session'):
            session['access_token'] = data['session'].access_token
            session['refresh_token'] = data['session'].refresh_token
            session['user_id'] = str(data['user'].id)
            return redirect(url_for('index'))
        else:
            # Email confirmation required
            return render_template('login.html',
                message='Account created! Please check your email to confirm your account, then sign in.')
    else:
        error_msg = data.get('error', 'Failed to create account')
        return render_template('signup.html', error=error_msg)


@app.route('/logout')
def logout():
    """Logout handler"""
    sign_out()
    return redirect(url_for('login'))


# Main App Routes (All require authentication)

@app.route('/')
@require_auth
def index():
    """Main page - requires authentication"""
    user = get_current_user()
    return render_template('index.html', user=user)


@app.route('/upload', methods=['POST'])
@require_auth
def upload_files():
    """Handle file uploads and scan mail - requires authentication"""
    user = get_current_user()

    if 'files[]' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    files = request.files.getlist('files[]')

    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400

    # Check scan limit before processing
    success, subscription = get_user_subscription(user.id)
    if not success:
        return jsonify({'error': 'Failed to get subscription information'}), 500

    # Check if user can scan
    can_scan_success, can_scan = can_user_scan(user.id)
    if not can_scan:
        plan_info = get_plan_info(subscription.get('plan_type', 'free'))
        return jsonify({
            'error': 'Scan limit reached',
            'message': f'You have reached your monthly limit of {plan_info["scan_limit"]} scans. Please upgrade your plan to continue scanning.',
            'current_plan': subscription.get('plan_type', 'free'),
            'scans_used': subscription.get('scans_this_month', 0),
            'scan_limit': plan_info['scan_limit'],
            'upgrade_url': url_for('account')
        }), 403

    scanned_count = 0
    errors = []
    total_files = len(files)
    created_results = []

    print(f"\n{'='*60}")
    print(f"User: {user.email}")
    print(f"Plan: {subscription.get('plan_type', 'free').upper()}")
    print(f"Scans this month: {subscription.get('scans_this_month', 0)}")
    print(f"Starting batch upload: {total_files} files")
    print(f"{'='*60}\n")

    for idx, file in enumerate(files, 1):
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                print(f"[{idx}/{total_files}] Processing: {filename}")

                # Process image in-memory (no disk storage)
                # Read file into BytesIO for in-memory processing
                image_bytes = BytesIO(file.read())
                image_bytes.seek(0)  # Reset pointer to beginning

                # Scan the mail (scanner now accepts file-like objects)
                scan_result = scanner.scan_mail(image_bytes)

                # Free memory immediately after processing
                image_bytes.close()
                del image_bytes
                gc.collect()

                print(f"[{idx}/{total_files}] ✓ Completed: {filename}")
                print(f"    Category: {scan_result.get('category', 'Unknown')}")
                print(f"    Sender: {scan_result.get('sender_name', 'Not found')}")

                # Show verification status
                verification_status = scan_result.get('verification_status', 'unknown')
                if verification_status == 'verified':
                    print(f"    ✓ Address Verified by Smarty")
                    if scan_result.get('verified_full_address'):
                        print(f"    Verified Address: {scan_result.get('verified_full_address')}")
                elif verification_status == 'verified_missing_secondary':
                    print(f"    ⚠ Address Verified (missing secondary/unit info)")
                elif verification_status in ['invalid', 'failed']:
                    print(f"    ✗ Address Verification Failed")
                elif verification_status == 'insufficient_data':
                    print(f"    ⊘ Insufficient address data for verification")

                print()

                # Save to Supabase database
                scan_data = {
                    'filename': filename,
                    'sender_name': scan_result.get('sender_name'),
                    'street': scan_result.get('street'),
                    'city': scan_result.get('city'),
                    'state': scan_result.get('state'),
                    'zip': scan_result.get('zip'),
                    'full_address': scan_result.get('full_address'),
                    'category': scan_result.get('category'),
                    'method': scan_result.get('method'),
                    'verified': scan_result.get('verified'),
                    'verification_status': scan_result.get('verification_status'),
                    'verified_street': scan_result.get('verified_street'),
                    'verified_city': scan_result.get('verified_city'),
                    'verified_state': scan_result.get('verified_state'),
                    'verified_zip': scan_result.get('verified_zip'),
                    'verified_full_address': scan_result.get('verified_full_address')
                }

                success, db_result = create_scan_result(user.id, scan_data)

                if success:
                    created_results.append(db_result)
                    scanned_count += 1

                    # Increment scan count for the user
                    increment_scan_count(user.id)
                else:
                    errors.append(f"{filename}: Failed to save to database")

            except Exception as e:
                import traceback
                error_msg = f"{file.filename}: {str(e)}"
                print(f"ERROR processing {file.filename}:")
                print(traceback.format_exc())
                errors.append(error_msg)
        else:
            errors.append(f"{file.filename}: Invalid file type")

    print(f"\n{'='*60}")
    print(f"Batch complete: {scanned_count}/{total_files} files processed successfully")
    if errors:
        print(f"Errors: {len(errors)}")
    print(f"{'='*60}\n")

    # Get all user results for the response
    success, all_results = get_user_scan_results(user.id)

    response = {
        'success': True,
        'scanned_count': scanned_count,
        'total_files': total_files,
        'total_results': len(all_results) if success else 0,
        'results': all_results if success else []
    }

    if errors:
        response['errors'] = errors

    return jsonify(response)


@app.route('/check-address', methods=['POST'])
@require_auth
def check_address():
    """Quick check if camera frame contains a readable address"""
    try:
        if 'frame' not in request.files:
            return jsonify({'has_address': False})

        frame = request.files['frame']

        if not frame or frame.filename == '':
            return jsonify({'has_address': False})

        # Process frame in-memory
        image_bytes = BytesIO(frame.read())
        image_bytes.seek(0)

        # Use a lightweight check - just extract text and see if it looks like an address
        import google.generativeai as genai
        import os
        from PIL import Image

        # Configure Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Load image
        image = Image.open(image_bytes)

        # Quick prompt to check for address
        prompt = """Look at this image. Does it contain a clearly readable mailing address (street, city, state, zip)?
Respond with ONLY 'YES' if you can see a complete, readable address.
Respond with ONLY 'NO' if the address is unclear, incomplete, or missing."""

        response = model.generate_content([prompt, image])
        result_text = response.text.strip().upper()

        # Clean up
        image.close()
        image_bytes.close()
        del image
        del image_bytes
        gc.collect()

        has_address = 'YES' in result_text

        return jsonify({'has_address': has_address})

    except Exception as e:
        print(f"Error checking for address: {e}")
        return jsonify({'has_address': False})


@app.route('/results')
@require_auth
def get_results():
    """Get all scanned results for the current user"""
    user = get_current_user()
    success, results = get_user_scan_results(user.id)

    if success:
        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        })
    else:
        return jsonify({
            'success': False,
            'error': results.get('error', 'Failed to get results')
        }), 500


@app.route('/clear')
@require_auth
def clear_results():
    """Clear all results for the current user"""
    user = get_current_user()
    success, data = clear_user_scan_results(user.id)

    if success:
        return jsonify({
            'success': True,
            'message': 'All results cleared'
        })
    else:
        return jsonify({
            'success': False,
            'error': data.get('error', 'Failed to clear results')
        }), 500


@app.route('/delete/<result_id>')
@require_auth
def delete_result(result_id):
    """Delete a specific result"""
    user = get_current_user()
    success, data = delete_scan_result(user.id, result_id)

    if success:
        # Get updated count
        success, results = get_user_scan_results(user.id)
        count = len(results) if success else 0

        return jsonify({
            'success': True,
            'message': 'Result deleted',
            'count': count
        })
    else:
        return jsonify({
            'success': False,
            'error': data.get('error', 'Failed to delete result')
        }), 500


@app.route('/export/csv')
@require_auth
def export_csv():
    """Export results to CSV"""
    user = get_current_user()
    success, results = get_user_scan_results(user.id)

    if not success or not results:
        return jsonify({'error': 'No results to export'}), 400

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Select and order columns
    columns = ['filename', 'sender_name', 'street', 'city', 'state', 'zip', 'full_address',
               'verified', 'verification_status', 'verified_street', 'verified_city',
               'verified_state', 'verified_zip', 'verified_full_address',
               'category', 'uploaded_at']
    df = df[[col for col in columns if col in df.columns]]

    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f'mail_scan_results_{timestamp}.csv'
    csv_path = os.path.join(app.config['EXPORT_FOLDER'], csv_filename)

    # Save CSV
    df.to_csv(csv_path, index=False)

    return send_file(
        csv_path,
        mimetype='text/csv',
        as_attachment=True,
        download_name=csv_filename
    )


@app.route('/export/excel')
@require_auth
def export_excel():
    """Export results to Excel"""
    user = get_current_user()
    success, results = get_user_scan_results(user.id)

    if not success or not results:
        return jsonify({'error': 'No results to export'}), 400

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Select and order columns
    columns = ['filename', 'sender_name', 'street', 'city', 'state', 'zip', 'full_address',
               'verified', 'verification_status', 'verified_street', 'verified_city',
               'verified_state', 'verified_zip', 'verified_full_address',
               'category', 'uploaded_at']
    df = df[[col for col in columns if col in df.columns]]

    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_filename = f'mail_scan_results_{timestamp}.xlsx'
    excel_path = os.path.join(app.config['EXPORT_FOLDER'], excel_filename)

    # Save Excel
    df.to_excel(excel_path, index=False, engine='openpyxl')

    return send_file(
        excel_path,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=excel_filename
    )


@app.route('/export/print-pdf')
@require_auth
def export_print_pdf():
    """Export selected addresses to PDF for printing"""
    user = get_current_user()

    # Get selected IDs from query params
    ids_param = request.args.get('ids', '')
    if not ids_param:
        return jsonify({'error': 'No addresses selected'}), 400

    selected_ids = ids_param.split(',')

    # Load all results and filter by selected IDs
    success, all_results = get_user_scan_results(user.id)

    if not success:
        return jsonify({'error': 'Failed to get results'}), 500

    selected_results = [r for r in all_results if str(r.get('id')) in selected_ids]

    if not selected_results:
        return jsonify({'error': 'No valid addresses found'}), 400

    # Generate PDF
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pdf_filename = f'address_labels_{timestamp}.pdf'
    pdf_path = os.path.join(app.config['EXPORT_FOLDER'], pdf_filename)

    # Create PDF with address labels
    create_address_pdf(selected_results, pdf_path)

    return send_file(
        pdf_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=pdf_filename
    )


def create_address_pdf(addresses, output_path):
    """Create a PDF with formatted addresses for printing"""
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    # Standard address label dimensions (Avery 5160 compatible: 3 across, 10 down)
    label_width = 2.625 * inch
    label_height = 1.0 * inch
    left_margin = 0.1875 * inch
    top_margin = 0.5 * inch
    cols = 3
    rows = 10
    labels_per_page = cols * rows

    page_num = 0
    for idx, addr in enumerate(addresses):
        # Calculate position
        label_idx = idx % labels_per_page
        col = label_idx % cols
        row = label_idx // cols

        # Start new page if needed
        if idx > 0 and label_idx == 0:
            c.showPage()
            page_num += 1

        # Calculate label position (top-left corner)
        x = left_margin + (col * label_width)
        y = height - top_margin - ((row + 1) * label_height)

        # Build address lines
        # Use verified address if available, otherwise use extracted address
        use_verified = addr.get('verified') and addr.get('verified_full_address')

        address_lines = []

        if addr.get('sender_name'):
            address_lines.append(addr['sender_name'])

        if use_verified:
            # Use verified address components
            if addr.get('verified_street'):
                address_lines.append(addr['verified_street'])

            city_state_zip = []
            if addr.get('verified_city'):
                city_state_zip.append(addr['verified_city'])
            if addr.get('verified_state'):
                city_state_zip.append(addr['verified_state'])
            if addr.get('verified_zip'):
                city_state_zip.append(addr['verified_zip'])

            if city_state_zip:
                address_lines.append(', '.join(city_state_zip))
        else:
            # Use original extracted address
            if addr.get('street'):
                address_lines.append(addr['street'])

            city_state_zip = []
            if addr.get('city'):
                city_state_zip.append(addr['city'])
            if addr.get('state'):
                city_state_zip.append(addr['state'])
            if addr.get('zip'):
                city_state_zip.append(addr['zip'])

            if city_state_zip:
                address_lines.append(', '.join(city_state_zip))

        # Draw address on label (centered vertically within label)
        line_height = 12
        total_text_height = len(address_lines) * line_height
        start_y = y + (label_height + total_text_height) / 2 - line_height

        c.setFont("Helvetica", 10)
        for i, line in enumerate(address_lines):
            text_y = start_y - (i * line_height)
            c.drawString(x + 5, text_y, line)

    c.save()


# Account & Subscription Routes

@app.route('/account')
@require_auth
def account():
    """Account management page"""
    user = get_current_user()
    success, subscription = get_user_subscription(user.id)

    return render_template('account.html',
                           user=user,
                           subscription=subscription if success else None,
                           stripe_key=STRIPE_PUBLISHABLE_KEY,
                           plans=get_all_plans())


@app.route('/api/subscription')
@require_auth
def get_subscription_api():
    """Get user subscription via API"""
    user = get_current_user()
    success, subscription = get_user_subscription(user.id)

    if success:
        # Get plan information
        plan_info = get_plan_info(subscription.get('plan_type', 'free'))

        return jsonify({
            'success': True,
            'subscription': subscription,
            'plan_info': plan_info
        })
    else:
        return jsonify({
            'success': False,
            'error': subscription.get('error', 'Failed to get subscription')
        }), 500


@app.route('/api/create-checkout-session', methods=['POST'])
@require_auth
def create_checkout_session_api():
    """Create a Stripe checkout session"""
    user = get_current_user()

    try:
        data = request.json
        plan_type = data.get('plan_type')

        if not plan_type or plan_type not in ['starter', 'growth', 'scale']:
            return jsonify({'error': 'Invalid plan type'}), 400

        # Get plan info
        plan_info = get_plan_info(plan_type)
        price_id = plan_info.get('stripe_price_id')

        if not price_id:
            return jsonify({'error': 'Plan not configured. Please add STRIPE_PRO_PRICE_ID and STRIPE_BUSINESS_PRICE_ID to your .env file'}), 500

        # Get or create Stripe customer
        success, subscription = get_user_subscription(user.id)

        if not success or not subscription.get('stripe_customer_id'):
            # Create new Stripe customer
            customer = create_customer(user.email, user.id)
            customer_id = customer.id

            # Update subscription with customer ID
            update_user_subscription(user.id, {'stripe_customer_id': customer_id})
        else:
            customer_id = subscription['stripe_customer_id']

        # Create checkout session
        success_url = url_for('account', _external=True) + '?success=true'
        cancel_url = url_for('account', _external=True) + '?cancelled=true'

        checkout_session = create_checkout_session(
            customer_id,
            price_id,
            success_url,
            cancel_url
        )

        return jsonify({
            'success': True,
            'sessionId': checkout_session.id
        })

    except Exception as e:
        print(f"Error creating checkout session: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/cancel-subscription', methods=['POST'])
@require_auth
def cancel_subscription_api():
    """Cancel user subscription"""
    user = get_current_user()

    try:
        success, subscription = get_user_subscription(user.id)

        if not success or not subscription.get('stripe_subscription_id'):
            return jsonify({'error': 'No active subscription found'}), 400

        # Cancel subscription at period end
        cancel_subscription(subscription['stripe_subscription_id'], at_period_end=True)

        # Update database
        update_user_subscription(user.id, {'status': 'cancelled'})

        return jsonify({
            'success': True,
            'message': 'Subscription will be cancelled at the end of the billing period'
        })

    except Exception as e:
        print(f"Error cancelling subscription: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/customer-portal', methods=['POST'])
@require_auth
def customer_portal():
    """Create Stripe Customer Portal session"""
    user = get_current_user()

    try:
        success, subscription = get_user_subscription(user.id)

        if not success or not subscription.get('stripe_customer_id'):
            return jsonify({'error': 'No Stripe customer found'}), 400

        return_url = url_for('account', _external=True)
        portal_session = create_customer_portal_session(
            subscription['stripe_customer_id'],
            return_url
        )

        return jsonify({
            'success': True,
            'url': portal_session.url
        })

    except Exception as e:
        print(f"Error creating portal session: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = construct_webhook_event(payload, sig_header)
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 400

    # Handle different event types
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session_completed(session)

    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)

    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_payment_failed(invoice)

    return jsonify({'success': True})


def handle_checkout_session_completed(session):
    """Handle successful checkout"""
    customer_id = session['customer']
    subscription_id = session['subscription']

    # Get subscription details from Stripe
    stripe_subscription = get_subscription(subscription_id)

    # Find user by customer ID
    # Note: This requires a database lookup
    # For now, we'll handle this in the webhook

    print(f"Checkout completed for customer {customer_id}, subscription {subscription_id}")


def handle_subscription_updated(subscription):
    """Handle subscription updates"""
    customer_id = subscription['customer']
    subscription_id = subscription['id']
    status = subscription['status']

    # Determine plan type from price ID
    price_id = subscription['items']['data'][0]['price']['id']
    plan_type = 'pro'  # Default

    # Map price ID to plan type
    starter_price_id = os.getenv('STRIPE_STARTER_PRICE_ID')
    growth_price_id = os.getenv('STRIPE_GROWTH_PRICE_ID')
    scale_price_id = os.getenv('STRIPE_SCALE_PRICE_ID')

    if price_id == starter_price_id:
        plan_type = 'starter'
    elif price_id == growth_price_id:
        plan_type = 'growth'
    elif price_id == scale_price_id:
        plan_type = 'scale'

    print(f"Subscription updated: {subscription_id}, status: {status}, plan: {plan_type}")


def handle_subscription_deleted(subscription):
    """Handle subscription cancellation"""
    subscription_id = subscription['id']
    print(f"Subscription deleted: {subscription_id}")


def handle_payment_failed(invoice):
    """Handle failed payment"""
    customer_id = invoice['customer']
    print(f"Payment failed for customer {customer_id}")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("MAIL SCANNER WEB APP WITH SUPABASE")
    print("="*60)

    # Use PORT from environment (for production) or default to 5001 (for local dev)
    port = int(os.getenv('PORT', 5001))

    print(f"Starting server at http://localhost:{port}")
    print("Press Ctrl+C to stop")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=port)
