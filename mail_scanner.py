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


class MailScanner:
    """
    Scans photos of mail to extract return address and sender name.
    """

    def __init__(self, gemini_api_key: Optional[str] = None, use_gemini: bool = True):
        """
        Initialize the mail scanner.

        Args:
            gemini_api_key: API key for Gemini. If None, reads from GEMINI_API_KEY env var
            use_gemini: Whether to use Gemini as primary OCR method (default: True)
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

    def scan_mail(self, image_path: str) -> Dict[str, Optional[str]]:
        """
        Scan a mail photo and extract sender information.

        Args:
            image_path: Path to the mail image file

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
                'method': 'gemini' or 'tesseract'
            }
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        if self.use_gemini:
            return self._scan_with_gemini(image_path)
        elif TESSERACT_AVAILABLE:
            return self._scan_with_tesseract(image_path)
        else:
            raise RuntimeError("No OCR method available. Install google-generativeai or pytesseract.")

    def _scan_with_gemini(self, image_path: str) -> Dict[str, Optional[str]]:
        """
        Use Gemini Vision API to extract sender information.
        """
        try:
            # Load and prepare image
            image = Image.open(image_path)

            # Create prompt for Gemini
            prompt = """
            Analyze this image of mail (envelope, postcard, package, or letter) and extract the sender's information:

            1. **Sender Name**:
               - First, check the return address (usually top-left corner of envelope)
               - If no name is in the return address, look inside the letter for:
                 * Signature at the bottom
                 * Name in the closing (e.g., "Sincerely, [Name]")
                 * Letterhead at the top
                 * "From:" line
               - Use context clues to identify the sender's name accurately

            2. **Return Address**: Extract from the envelope/letter:
               - Street Address
               - City
               - State
               - ZIP Code

            3. **Mail Category**: Identify the type/category of this mail based on visual cues, text content, and context:
               - "Graduation Announcement" - graduation-related content, formal announcements
               - "Wedding Invitation" - wedding invitations, save the dates, RSVP cards
               - "Baby Announcement" - birth announcements, baby shower invitations
               - "Fan Letters" - letters praising a product, service, or expressing appreciation
               - "Other" - anything that doesn't fit the above categories

            Return the information in JSON format with these exact keys:
            {
                "sender_name": "full name here or null if not found",
                "street": "street address or null if not found",
                "city": "city or null if not found",
                "state": "state abbreviation or full name",
                "zip": "zip code or null if not found",
                "category": "one of the categories listed above"
            }

            Important:
            - Extract ONLY the sender's information, NOT the recipient/destination
            - The return address is usually in the top-left corner of an envelope
            - For the sender name, prioritize: return address name > signature > letterhead > closing
            - For category, look at visual design, text content, and overall purpose
            - Handle handwriting and various fonts
            - If any field is not clearly visible, use null
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

    def _scan_with_tesseract(self, image_path: str) -> Dict[str, Optional[str]]:
        """
        Use Tesseract OCR to extract text and parse sender information.
        This is a fallback method and may be less accurate than Gemini.
        """
        try:
            # Load image
            image = Image.open(image_path)

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
