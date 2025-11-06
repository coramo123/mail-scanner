"""
Supabase Client Module
Handles authentication and database operations for the Mail Scanner app
"""

import os
from dotenv import load_dotenv
from functools import wraps
from flask import session, redirect, url_for, jsonify

# Load environment variables FIRST
load_dotenv()

# Disable HTTP/2 BEFORE any imports
os.environ['HTTPX_HTTP2'] = '0'
os.environ['HTTPCORE_HTTP2'] = '0'

# Monkey-patch httpx to force HTTP/1.1
import httpx
import httpcore

# Store original Client class
_original_httpx_client = httpx.Client
_original_async_client = httpx.AsyncClient

# Create wrapper that forces HTTP/1.1
class PatchedClient(_original_httpx_client):
    def __init__(self, *args, **kwargs):
        kwargs['http2'] = False
        kwargs['http1'] = True
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 60.0
        super().__init__(*args, **kwargs)

class PatchedAsyncClient(_original_async_client):
    def __init__(self, *args, **kwargs):
        kwargs['http2'] = False
        kwargs['http1'] = True
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 60.0
        super().__init__(*args, **kwargs)

# Replace httpx.Client with patched version
httpx.Client = PatchedClient
httpx.AsyncClient = PatchedAsyncClient

print("✓ HTTP/2 disabled globally via monkey-patch")

# Now import supabase after patching httpx
from supabase import create_client, Client

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "Missing Supabase credentials. "
        "Please set SUPABASE_URL and SUPABASE_KEY in your .env file. "
        "See SUPABASE_SETUP.md for instructions."
    )

# Initialize Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Supabase client initialized successfully")
except Exception as e:
    print(f"✗ Error initializing Supabase client: {e}")
    raise


def get_current_user():
    """Get the current authenticated user from session with auto-refresh"""
    access_token = session.get('access_token')
    if not access_token:
        return None

    try:
        # Verify and get user from token
        user_response = supabase.auth.get_user(access_token)
        return user_response.user
    except Exception as e:
        error_msg = str(e)
        print(f"Error getting current user: {error_msg}")

        # If token expired, try to refresh
        if "expired" in error_msg.lower() or "invalid" in error_msg.lower():
            print("Token expired, attempting to refresh session...")
            try:
                # Get refresh token from session
                refresh_token = session.get('refresh_token')
                if refresh_token:
                    # Refresh the session
                    refresh_response = supabase.auth.refresh_session(refresh_token)
                    if refresh_response and refresh_response.session:
                        # Update session with new tokens
                        session['access_token'] = refresh_response.session.access_token
                        session['refresh_token'] = refresh_response.session.refresh_token
                        print("✓ Session refreshed successfully")
                        return refresh_response.user
            except Exception as refresh_error:
                print(f"Failed to refresh session: {refresh_error}")

        # Clear invalid session
        session.clear()
        return None


def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if user is None:
            # Return JSON for API endpoints
            if '/api/' in str(f):
                return jsonify({'error': 'Authentication required'}), 401
            # Redirect to login for page routes
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Authentication Functions

def sign_up(email, password):
    """
    Create a new user account
    Returns: (success: bool, data/error: dict)
    """
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        if response.user:
            return True, {
                'user': response.user,
                'session': response.session
            }
        else:
            return False, {'error': 'Failed to create account'}

    except Exception as e:
        return False, {'error': str(e)}


def sign_in(email, password):
    """
    Sign in an existing user with retry logic
    Returns: (success: bool, data/error: dict)
    """
    import time

    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            print(f"Login attempt {attempt + 1}/{max_retries}")

            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if response.user and response.session:
                print("✓ Login successful")
                return True, {
                    'user': response.user,
                    'session': response.session,
                    'access_token': response.session.access_token
                }
            else:
                return False, {'error': 'Invalid credentials'}

        except Exception as e:
            error_msg = str(e)
            print(f"Login error on attempt {attempt + 1}: {error_msg}")

            # Handle specific error types
            is_connection_error = (
                "StreamReset" in error_msg or
                "stream_id" in error_msg or
                "RemoteProtocolError" in error_msg or
                "ConnectionError" in error_msg
            )

            if is_connection_error and attempt < max_retries - 1:
                # Retry on connection errors
                print(f"Connection error, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            elif is_connection_error:
                return False, {'error': 'Connection error after multiple attempts. Please try again later.'}
            elif "timeout" in error_msg.lower():
                return False, {'error': 'Request timed out. Please try again.'}
            elif "invalid" in error_msg.lower() or "password" in error_msg.lower():
                return False, {'error': 'Invalid email or password'}
            else:
                return False, {'error': error_msg}

    return False, {'error': 'Failed to sign in after multiple attempts'}


def sign_out():
    """Sign out the current user"""
    try:
        supabase.auth.sign_out()
        session.clear()
        return True, {'message': 'Signed out successfully'}
    except Exception as e:
        return False, {'error': str(e)}


# Database Functions for Scan Results

def create_scan_result(user_id, scan_data):
    """
    Create a new scan result in the database
    Args:
        user_id: UUID of the user
        scan_data: Dictionary containing scan result data
    Returns: (success: bool, data/error: dict)
    """
    try:
        # Prepare data for database
        db_data = {
            'user_id': str(user_id),
            'filename': scan_data.get('filename'),
            'sender_name': scan_data.get('sender_name'),
            'street': scan_data.get('street'),
            'city': scan_data.get('city'),
            'state': scan_data.get('state'),
            'zip': scan_data.get('zip'),
            'full_address': scan_data.get('full_address'),
            'category': scan_data.get('category'),
            'method': scan_data.get('method'),
            'verified': scan_data.get('verified', False),
            'verification_status': scan_data.get('verification_status'),
            'verified_street': scan_data.get('verified_street'),
            'verified_city': scan_data.get('verified_city'),
            'verified_state': scan_data.get('verified_state'),
            'verified_zip': scan_data.get('verified_zip'),
            'verified_full_address': scan_data.get('verified_full_address')
        }

        response = supabase.table('scan_results').insert(db_data).execute()

        if response.data:
            return True, response.data[0]
        else:
            return False, {'error': 'Failed to save scan result'}

    except Exception as e:
        print(f"Error creating scan result: {e}")
        return False, {'error': str(e)}


def get_user_scan_results(user_id):
    """
    Get all scan results for a user
    Returns: (success: bool, data/error: list/dict)
    """
    try:
        response = supabase.table('scan_results') \
            .select('*') \
            .eq('user_id', str(user_id)) \
            .order('uploaded_at', desc=True) \
            .execute()

        return True, response.data

    except Exception as e:
        print(f"Error getting scan results: {e}")
        return False, {'error': str(e)}


def delete_scan_result(user_id, result_id):
    """
    Delete a specific scan result
    Returns: (success: bool, data/error: dict)
    """
    try:
        # RLS policies will ensure user can only delete their own results
        response = supabase.table('scan_results') \
            .delete() \
            .eq('id', result_id) \
            .eq('user_id', str(user_id)) \
            .execute()

        return True, {'message': 'Scan result deleted'}

    except Exception as e:
        print(f"Error deleting scan result: {e}")
        return False, {'error': str(e)}


def clear_user_scan_results(user_id):
    """
    Delete all scan results for a user
    Returns: (success: bool, data/error: dict)
    """
    try:
        response = supabase.table('scan_results') \
            .delete() \
            .eq('user_id', str(user_id)) \
            .execute()

        return True, {'message': 'All scan results cleared'}

    except Exception as e:
        print(f"Error clearing scan results: {e}")
        return False, {'error': str(e)}
