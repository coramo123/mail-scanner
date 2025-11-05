"""
Supabase Client Module
Handles authentication and database operations for the Mail Scanner app
"""

import os
from dotenv import load_dotenv
from functools import wraps
from flask import session, redirect, url_for, jsonify
import httpx

# Load environment variables FIRST
load_dotenv()

# Disable HTTP/2 BEFORE any imports that use httpx
os.environ['HTTPX_HTTP2'] = 'false'
os.environ['HTTPCORE_HTTP2'] = 'false'

# Now import supabase after setting environment variables
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

# Create a custom httpx client with HTTP/1.1 only
http_client = httpx.Client(
    timeout=60.0,
    limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
    http1=True,  # Force HTTP/1.1
    http2=False  # Disable HTTP/2
)

# Initialize Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Supabase client initialized successfully")
except Exception as e:
    print(f"✗ Error initializing Supabase client: {e}")
    raise


def get_current_user():
    """Get the current authenticated user from session"""
    access_token = session.get('access_token')
    if not access_token:
        return None

    try:
        # Verify and get user from token
        user_response = supabase.auth.get_user(access_token)
        return user_response.user
    except Exception as e:
        print(f"Error getting current user: {e}")
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
    Sign in an existing user
    Returns: (success: bool, data/error: dict)
    """
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user and response.session:
            return True, {
                'user': response.user,
                'session': response.session,
                'access_token': response.session.access_token
            }
        else:
            return False, {'error': 'Invalid credentials'}

    except Exception as e:
        error_msg = str(e)
        print(f"Login error: {error_msg}")

        # Handle specific error types
        if "StreamReset" in error_msg or "stream_id" in error_msg:
            return False, {'error': 'Connection error. Please try again.'}
        elif "timeout" in error_msg.lower():
            return False, {'error': 'Request timed out. Please try again.'}
        else:
            return False, {'error': error_msg}


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
