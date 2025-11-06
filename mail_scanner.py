"""
Mail Scanner - Extract sender information from mail photos
Supports both Gemini Vision API (primary) and Tesseract OCR (fallback)
"""

import os
import base64
import json
from typing import Dict, Optional, Tuple
from pathlib import Path
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Gemini features will be unavailable.")

try:
    from PIL import Image
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Warning: PIL or pytesseract not installed. Tesseract features will be unavailable.")

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()  # Register HEIC/HEIF support with Pillow
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False
    print("Warning: pillow-heif not installed. HEIC/HEIF files may not be supported.")

try:
    from smartystreets_python_sdk import StaticCredentials, exceptions, ClientBuilder
    from smartystreets_python_sdk.us_street import Lookup as StreetLookup
    SMARTY_AVAILABLE = True
except ImportError:
    SMARTY_AVAILABLE = False
    print("Warning: smartystreets-python-sdk not installed. Address verification will be unavailable.")


class MailScanner:
    """
    Scans photos of mail to extract return address and sender name.
    """

    def __init__(self, gemini_api_key: Optional[str] = None, use_gemini: bool = True,
                 smarty_auth_id: Optional[str] = None, smarty_auth_token: Optional[str] = None,
                 use_smarty: bool = True):
        """
        Initialize the mail scanner.

        Args:
            gemini_api_key: API key for Gemini. If None, reads from GEMINI_API_KEY env var
            use_gemini: Whether to use Gemini as primary OCR method (default: True)
            smarty_auth_id: Smarty auth ID. If None, reads from SMARTY_AUTH_ID env var
            smarty_auth_token: Smarty auth token. If None, reads from SMARTY_AUTH_TOKEN env var
            use_smarty: Whether to use Smarty for address verification (default: True)
        """
        self.use_gemini = use_gemini and GEMINI_AVAILABLE

        if self.use_gemini:
            api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
            if not api_key:
                print("Warning: No Gemini API key provided. Falling back to Tesseract.")
                self.use_gemini = False
            else:
                genai.configure(api_key=api_key)
                # Use latest Gemini model with vision support
                self.model = genai.GenerativeModel('gemini-2.5-flash')

        # Initialize Smarty address verification
        self.use_smarty = use_smarty and SMARTY_AVAILABLE
        self.smarty_client = None

        if self.use_smarty:
            auth_id = smarty_auth_id or os.getenv('SMARTY_AUTH_ID')
            auth_token = smarty_auth_token or os.getenv('SMARTY_AUTH_TOKEN')

            if not auth_id or not auth_token:
                print("Warning: No Smarty credentials provided. Address verification will be disabled.")
                self.use_smarty = False
            else:
                credentials = StaticCredentials(auth_id, auth_token)
                self.smarty_client = ClientBuilder(credentials).build_us_street_api_client()

    def scan_mail(self, image_source) -> Dict[str, Optional[str]]:
        """
        Scan a mail photo and extract sender information.

        Args:
            image_source: Either a file path (str/Path) or a file-like object (BytesIO, file upload)

        Returns:
            Dictionary with extracted information:
            {
                'sender_name': str or None,
                'street': str or None,
                'city': str or None,
                'state': str or None,
                'zip': str or None,
                'full_address': str or None,
                'category': str or None,
                'method': 'gemini' or 'tesseract',
                'verified': bool or None,
                'verification_status': str or None,
                'verified_street': str or None,
                'verified_city': str or None,
                'verified_state': str or None,
                'verified_zip': str or None,
                'verified_full_address': str or None
            }
        """
        # Check if it's a file path
        if isinstance(image_source, (str, Path)):
            if not os.path.exists(image_source):
                raise FileNotFoundError(f"Image file not found: {image_source}")

        # Extract address using OCR
        if self.use_gemini:
            result = self._scan_with_gemini(image_source)
        elif TESSERACT_AVAILABLE:
            result = self._scan_with_tesseract(image_source)
        else:
            raise RuntimeError("No OCR method available. Install google-generativeai or pytesseract.")

        # Verify address with Smarty if enabled
        if self.use_smarty:
            verification_result = self.verify_address(
                street=result.get('street'),
                city=result.get('city'),
                state=result.get('state'),
                zipcode=result.get('zip')
            )
            result.update(verification_result)
        else:
            # Add default verification fields when Smarty is not used
            result.update({
                'verified': None,
                'verification_status': 'not_attempted',
                'verified_street': None,
                'verified_city': None,
                'verified_state': None,
                'verified_zip': None,
                'verified_full_address': None
            })

        return result

    def verify_address(self, street: Optional[str], city: Optional[str],
                      state: Optional[str], zipcode: Optional[str]) -> Dict[str, Optional[str]]:
        """
        Verify an address using Smarty address verification API.

        Args:
            street: Street address
            city: City name
            state: State abbreviation or full name
            zipcode: ZIP code

        Returns:
            Dictionary with verification results:
            {
                'verified': bool,
                'verification_status': str ('verified', 'invalid', 'ambiguous', 'error'),
                'verified_street': str or None,
                'verified_city': str or None,
                'verified_state': str or None,
                'verified_zip': str or None,
                'verified_full_address': str or None
            }
        """
        # Default response
        default_result = {
            'verified': False,
            'verification_status': 'error',
            'verified_street': None,
            'verified_city': None,
            'verified_state': None,
            'verified_zip': None,
            'verified_full_address': None
        }

        # Check if we have minimum required information
        if not street:
            default_result['verification_status'] = 'insufficient_data'
            return default_result

        if not self.smarty_client:
            default_result['verification_status'] = 'not_configured'
            return default_result

        try:
            # Create lookup
            lookup = StreetLookup()
            lookup.street = street
            lookup.city = city
            lookup.state = state
            lookup.zipcode = zipcode
            lookup.match = "invalid"  # Return result only if valid

            # Send to Smarty
            self.smarty_client.send_lookup(lookup)

            result = lookup.result

            if not result:
                # No match found - address is invalid
                return {
                    'verified': False,
                    'verification_status': 'invalid',
                    'verified_street': None,
                    'verified_city': None,
                    'verified_state': None,
                    'verified_zip': None,
                    'verified_full_address': None
                }

            # Get first candidate (Smarty returns best match)
            candidate = result[0]

            # Build verified address
            delivery_line = candidate.delivery_line_1
            last_line = candidate.last_line
            components = candidate.components

            verified_street = delivery_line
            verified_city = components.city_name
            verified_state = components.state_abbreviation
            verified_zip = f"{components.zipcode}-{components.plus4_code}" if components.plus4_code else components.zipcode

            # Build full address
            verified_full = f"{verified_street}, {verified_city}, {verified_state} {verified_zip}"

            # Determine verification status based on match quality
            analysis = candidate.analysis
            dpv_match_code = analysis.dpv_match_code

            if dpv_match_code == 'Y':
                verification_status = 'verified'
                verified = True
            elif dpv_match_code == 'D':
                verification_status = 'verified_missing_secondary'
                verified = True
            elif dpv_match_code == 'S':
                verification_status = 'verified_missing_secondary'
                verified = True
            else:
                verification_status = 'failed'
                verified = False

            return {
                'verified': verified,
                'verification_status': verification_status,
                'verified_street': verified_street,
                'verified_city': verified_city,
                'verified_state': verified_state,
                'verified_zip': verified_zip,
                'verified_full_address': verified_full
            }

        except exceptions.SmartyException as e:
            print(f"Smarty API error: {e}")
            return {
                'verified': False,
                'verification_status': 'error',
                'verified_street': None,
                'verified_city': None,
                'verified_state': None,
                'verified_zip': None,
                'verified_full_address': None
            }
        except Exception as e:
            print(f"Unexpected error during address verification: {e}")
            return default_result

    def _scan_with_gemini(self, image_source) -> Dict[str, Optional[str]]:
        """
        Use Gemini Vision API to extract sender information.
        Args:
            image_source: Either a file path or file-like object
        """
        try:
            # Load and prepare image (PIL Image.open works with both paths and file objects)
            image = Image.open(image_source)

            # Create prompt for Gemini
            prompt = """
            Analyze this image of mail and extract information about the PRIMARY SUBJECT of this mail:

            **CRITICAL - Who to Extract:**

            First, identify what type of mail this is:

            1. **For Announcements (Wedding, Graduation, Baby):**
               - Extract the name of the PRIMARY SUBJECT (the person/people to respond to)
               - Wedding Invitation → Extract the COUPLE'S names (bride and groom), NOT the parents announcing
               - Graduation Announcement → Extract the GRADUATE'S name, NOT the parents
               - Baby Announcement → Extract the MOTHER'S name (the parent, not the baby's name)
               - Look in the main body text, headlines, or featured names

            2. **For Regular Mail/Fan Letters:**
               - Extract the SENDER's name from:
                 * Return address (top-left corner)
                 * Signature at bottom
                 * Letterhead
                 * "From:" line

            **Return Address:**
            Always extract the return address (top-left corner of envelope) for mailing purposes:
            - Street Address
            - City
            - State
            - ZIP Code

            **Mail Category:**
            Identify the type based on visual cues and content:
            - "Wedding Invitation" - wedding invitations, save the dates, RSVP cards
            - "Graduation Announcement" - graduation announcements, grad party invites
            - "Baby Announcement" - birth announcements, baby shower invitations
            - "Fan Letters" - appreciation letters, fan mail
            - "Other" - anything else

            Return JSON with these exact keys:
            {
                "sender_name": "PRIMARY SUBJECT name (couple/graduate/mother) OR sender name for regular mail",
                "street": "return address street or null",
                "city": "return address city or null",
                "state": "return address state or null",
                "zip": "return address zip or null",
                "category": "one of the categories above"
            }

            IMPORTANT:
            - Wedding: sender_name = bride and groom's names
            - Graduation: sender_name = graduate's name
            - Baby announcement: sender_name = mother's name (not the baby)
            - Regular mail: sender_name = sender's name
            - Return address = always the mailing address (top-left corner)
            - If multiple people (like a couple), include both names
            - Handle handwriting and various fonts
            - If any field unclear, use null
            - Return ONLY the JSON object, no additional text
            """

            # Generate response
            response = self.model.generate_content([prompt, image])

            # Parse JSON from response
            result = self._parse_gemini_response(response.text)
            result['method'] = 'gemini'

            # Create full address string
            address_parts = [
                result.get('street'),
                result.get('city'),
                result.get('state'),
                result.get('zip')
            ]
            result['full_address'] = ', '.join(filter(None, address_parts)) or None

            return result

        except Exception as e:
            print(f"Gemini scan failed: {e}")
            if TESSERACT_AVAILABLE:
                print("Falling back to Tesseract...")
                return self._scan_with_tesseract(image_path)
            else:
                raise

    def _parse_gemini_response(self, response_text: str) -> Dict[str, Optional[str]]:
        """
        Parse JSON response from Gemini.
        """
        try:
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith('```'):
                response_text = re.sub(r'^```json?\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)

            # Parse JSON
            data = json.loads(response_text)

            return {
                'sender_name': data.get('sender_name'),
                'street': data.get('street'),
                'city': data.get('city'),
                'state': data.get('state'),
                'zip': data.get('zip'),
                'category': data.get('category')
            }
        except json.JSONDecodeError as e:
            print(f"Failed to parse Gemini response as JSON: {e}")
            print(f"Response text: {response_text}")
            return {
                'sender_name': None,
                'street': None,
                'city': None,
                'state': None,
                'zip': None,
                'category': None
            }

    def _scan_with_tesseract(self, image_source) -> Dict[str, Optional[str]]:
        """
        Use Tesseract OCR to extract text and parse sender information.
        This is a fallback method and may be less accurate than Gemini.
        Args:
            image_source: Either a file path or file-like object
        """
        try:
            # Load image (PIL Image.open works with both paths and file objects)
            image = Image.open(image_source)

            # Extract text with Tesseract
            text = pytesseract.image_to_string(image)

            # Parse the extracted text
            result = self._parse_address_text(text)
            result['method'] = 'tesseract'

            return result

        except Exception as e:
            print(f"Tesseract scan failed: {e}")
            raise

    def _parse_address_text(self, text: str) -> Dict[str, Optional[str]]:
        """
        Parse address information from raw OCR text.
        This is a basic implementation - Gemini is much better at this.
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        result = {
            'sender_name': None,
            'street': None,
            'city': None,
            'state': None,
            'zip': None,
            'full_address': None,
            'category': None
        }

        # Try to find ZIP code (5 digits or 5+4 format)
        zip_pattern = r'\b\d{5}(?:-\d{4})?\b'
        for line in lines:
            zip_match = re.search(zip_pattern, line)
            if zip_match:
                result['zip'] = zip_match.group()

                # Try to parse city, state from the same line
                # Common format: City, ST ZIP
                city_state_pattern = r'([^,]+),\s*([A-Z]{2})\s*\d{5}'
                cs_match = re.search(city_state_pattern, line)
                if cs_match:
                    result['city'] = cs_match.group(1).strip()
                    result['state'] = cs_match.group(2).strip()
                break

        # First non-empty line is often the sender name
        if lines:
            result['sender_name'] = lines[0]

        # Second line is often the street address
        if len(lines) > 1:
            result['street'] = lines[1]

        # Create full address
        address_parts = [
            result.get('street'),
            result.get('city'),
            result.get('state'),
            result.get('zip')
        ]
        result['full_address'] = ', '.join(filter(None, address_parts)) or None

        return result


def main():
    """
    Example usage of the MailScanner.
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python mail_scanner.py <image_path>")
        print("Example: python mail_scanner.py sample_mail.jpg")
        sys.exit(1)

    image_path = sys.argv[1]

    # Create scanner (will use Gemini if API key is set in environment)
    scanner = MailScanner()

    print(f"Scanning mail image: {image_path}")
    print("-" * 50)

    # Scan the mail
    result = scanner.scan_mail(image_path)

    # Display results
    print(f"Method used: {result['method']}")
    print(f"\nSender Name: {result['sender_name'] or 'Not found'}")
    print(f"Street: {result['street'] or 'Not found'}")
    print(f"City: {result['city'] or 'Not found'}")
    print(f"State: {result['state'] or 'Not found'}")
    print(f"ZIP: {result['zip'] or 'Not found'}")
    print(f"\nFull Address: {result['full_address'] or 'Not found'}")
    print(f"Mail Category: {result['category'] or 'Not found'}")


if __name__ == "__main__":
    main()
