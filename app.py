"""
Mail Scanner Web Application
Upload mail photos, scan for sender information, and export to spreadsheet
"""

from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import uuid
from mail_scanner import MailScanner
import pandas as pd
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

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

# Initialize mail scanner
scanner = MailScanner()


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_session_id():
    """Get or create session ID for storing results"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']


def get_session_file():
    """Get the path to the session's results file"""
    session_id = get_session_id()
    return os.path.join(app.config['UPLOAD_FOLDER'], f'results_{session_id}.json')


def load_results():
    """Load results from session file"""
    results_file = get_session_file()
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            return json.load(f)
    return []


def save_results(results):
    """Save results to session file"""
    results_file = get_session_file()
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads and scan mail"""
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    files = request.files.getlist('files[]')

    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400

    results = load_results()
    scanned_count = 0
    errors = []
    total_files = len(files)

    print(f"\n{'='*60}")
    print(f"Starting batch upload: {total_files} files")
    print(f"{'='*60}\n")

    for idx, file in enumerate(files, 1):
        if file and allowed_file(file.filename):
            try:
                # Save uploaded file
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)

                print(f"[{idx}/{total_files}] Processing: {filename}")

                # Scan the mail
                scan_result = scanner.scan_mail(filepath)

                print(f"[{idx}/{total_files}] ✓ Completed: {filename}")
                print(f"    Category: {scan_result.get('category', 'Unknown')}")
                print(f"    Sender: {scan_result.get('sender_name', 'Not found')}\n")

                # Add metadata
                result = {
                    'id': str(uuid.uuid4()),
                    'filename': filename,
                    'uploaded_at': datetime.now().isoformat(),
                    'sender_name': scan_result.get('sender_name'),
                    'street': scan_result.get('street'),
                    'city': scan_result.get('city'),
                    'state': scan_result.get('state'),
                    'zip': scan_result.get('zip'),
                    'full_address': scan_result.get('full_address'),
                    'category': scan_result.get('category'),
                    'method': scan_result.get('method')
                }

                results.append(result)
                scanned_count += 1

            except Exception as e:
                import traceback
                error_msg = f"{file.filename}: {str(e)}"
                print(f"ERROR processing {file.filename}:")
                print(traceback.format_exc())
                errors.append(error_msg)
        else:
            errors.append(f"{file.filename}: Invalid file type")

    # Save results
    save_results(results)

    print(f"\n{'='*60}")
    print(f"Batch complete: {scanned_count}/{total_files} files processed successfully")
    if errors:
        print(f"Errors: {len(errors)}")
    print(f"{'='*60}\n")

    response = {
        'success': True,
        'scanned_count': scanned_count,
        'total_files': total_files,
        'total_results': len(results),
        'results': results
    }

    if errors:
        response['errors'] = errors

    return jsonify(response)


@app.route('/results')
def get_results():
    """Get all scanned results"""
    results = load_results()
    return jsonify({
        'success': True,
        'count': len(results),
        'results': results
    })


@app.route('/clear')
def clear_results():
    """Clear all results"""
    results_file = get_session_file()
    if os.path.exists(results_file):
        os.remove(results_file)

    return jsonify({
        'success': True,
        'message': 'All results cleared'
    })


@app.route('/delete/<result_id>')
def delete_result(result_id):
    """Delete a specific result"""
    results = load_results()
    results = [r for r in results if r['id'] != result_id]
    save_results(results)

    return jsonify({
        'success': True,
        'message': 'Result deleted',
        'count': len(results)
    })


@app.route('/export/csv')
def export_csv():
    """Export results to CSV"""
    results = load_results()

    if not results:
        return jsonify({'error': 'No results to export'}), 400

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Select and order columns
    columns = ['filename', 'sender_name', 'street', 'city', 'state', 'zip', 'full_address', 'category', 'uploaded_at']
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
def export_excel():
    """Export results to Excel"""
    results = load_results()

    if not results:
        return jsonify({'error': 'No results to export'}), 400

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Select and order columns
    columns = ['filename', 'sender_name', 'street', 'city', 'state', 'zip', 'full_address', 'category', 'uploaded_at']
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
def export_print_pdf():
    """Export selected addresses to PDF for printing"""
    # Get selected IDs from query params
    ids_param = request.args.get('ids', '')
    if not ids_param:
        return jsonify({'error': 'No addresses selected'}), 400

    selected_ids = ids_param.split(',')

    # Load all results and filter by selected IDs
    all_results = load_results()
    selected_results = [r for r in all_results if r['id'] in selected_ids]

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
        address_lines = []

        if addr.get('sender_name'):
            address_lines.append(addr['sender_name'])

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


if __name__ == '__main__':
    print("\n" + "="*60)
    print("MAIL SCANNER WEB APP")
    print("="*60)
    print("Starting server at http://localhost:5001")
    print("Press Ctrl+C to stop")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5001)
