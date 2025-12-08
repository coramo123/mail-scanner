# Minute Mail

A Python tool that scans photos of mail (envelopes, postcards, packages) to extract return address information and sender names. Uses Google Gemini Vision API for accurate text extraction from handwriting and varied fonts, with Tesseract OCR as a fallback option.

## Features

- **Gemini Vision API Integration**: Leverages AI to accurately read handwriting and inconsistent fonts
- **Smarty Address Verification**: Validates and standardizes extracted addresses using Smarty's USPS database
- **Multi-format Support**: Handles envelopes, postcards, and packages with varying layouts
- **Tesseract Fallback**: Works offline with Tesseract OCR when Gemini is unavailable
- **Structured Output**: Returns sender name, street, city, state, and ZIP code
- **Address Correction**: Automatically corrects and standardizes addresses with Smarty verification
- **Easy to Use**: Simple API with both command-line and programmatic interfaces

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR (Optional, for fallback)

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

### 3. Configure API Keys

**Gemini API Key** (Required for OCR)
Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

**Smarty API Credentials** (Required for Address Verification)
Get your Smarty auth-id and auth-token from [Smarty](https://www.smarty.com/)

Create a `.env` file:
```bash
cp .env.example .env
```

Edit `.env` and add your API credentials:
```
GEMINI_API_KEY=your_actual_api_key_here
SMARTY_AUTH_ID=your_smarty_auth_id_here
SMARTY_AUTH_TOKEN=your_smarty_auth_token_here
```

## Usage

### Command Line

```bash
python minute_mail.py path/to/mail_photo.jpg
```

Example output:
```
Scanning mail image: sample_mail.jpg
--------------------------------------------------
Method used: gemini

Sender Name: John Smith
Street: 123 Main Street
City: Springfield
State: IL
ZIP: 62701

Full Address: 123 Main Street, Springfield, IL, 62701
Mail Category: Fan Letters

✓ Address Verified by Smarty
Verified Address: 123 Main St, Springfield, IL 62701-1234
```

### Python Code

```python
from minute_mail import MinuteMail
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create scanner
scanner = MinuteMail()

# Scan mail image
result = scanner.scan_mail("mail_photo.jpg")

# Access extracted information
print(f"Sender: {result['sender_name']}")
print(f"Address: {result['full_address']}")
print(f"ZIP: {result['zip']}")
```

### Return Format

The scanner returns a dictionary with the following structure:

```python
{
    # Extracted address information
    'sender_name': 'John Smith',           # or None if not found
    'street': '123 Main Street',           # or None if not found
    'city': 'Springfield',                 # or None if not found
    'state': 'IL',                         # or None if not found
    'zip': '62701',                        # or None if not found
    'full_address': '123 Main Street, Springfield, IL, 62701',
    'category': 'Fan Letters',             # Mail category
    'method': 'gemini',                    # 'gemini' or 'tesseract'

    # Smarty address verification results
    'verified': True,                      # Whether address was verified
    'verification_status': 'verified',     # Status: 'verified', 'invalid', 'insufficient_data', etc.
    'verified_street': '123 Main St',      # Standardized street address
    'verified_city': 'Springfield',        # Verified city name
    'verified_state': 'IL',                # Verified state abbreviation
    'verified_zip': '62701-1234',          # Verified ZIP+4
    'verified_full_address': '123 Main St, Springfield, IL 62701-1234'  # Complete verified address
}
```

**Verification Status Values:**
- `verified`: Address is valid and deliverable
- `verified_missing_secondary`: Valid but missing unit/apartment number
- `invalid`: Address could not be verified
- `insufficient_data`: Not enough address information to verify
- `not_attempted`: Smarty verification not configured
- `error`: Error occurred during verification

## Advanced Usage

### Disable Address Verification

```python
# Disable Smarty address verification
scanner = MinuteMail(use_smarty=False)
result = scanner.scan_mail("mail.jpg")
```

### Force Tesseract OCR

```python
# Use Tesseract instead of Gemini (for offline use)
scanner = MinuteMail(use_gemini=False)
result = scanner.scan_mail("mail.jpg")
```

### Explicit API Keys

```python
# Pass API keys directly instead of using .env
scanner = MinuteMail(
    gemini_api_key="your_gemini_key_here",
    smarty_auth_id="your_smarty_auth_id",
    smarty_auth_token="your_smarty_token"
)
```

### Access Verified Address

```python
scanner = MinuteMail()
result = scanner.scan_mail("mail.jpg")

# Check if address was verified
if result['verified']:
    print(f"Original: {result['full_address']}")
    print(f"Verified: {result['verified_full_address']}")
    print(f"Status: {result['verification_status']}")
else:
    print(f"Address could not be verified: {result['verification_status']}")
```

### Batch Processing

```python
scanner = MinuteMail()

mail_images = ["mail1.jpg", "mail2.jpg", "mail3.jpg"]
results = []

for image in mail_images:
    result = scanner.scan_mail(image)
    results.append(result)
```

See `example.py` for more detailed examples.

## How It Works

1. **Image Loading**: Loads the mail photo using PIL
2. **Gemini Vision API**: Sends image to Gemini with a structured prompt asking for return address information
3. **JSON Parsing**: Extracts structured data (name, street, city, state, ZIP) from Gemini's response
4. **Address Verification**: Sends extracted address to Smarty API for USPS validation and standardization
5. **Result Combination**: Returns both original extracted data and verified/corrected address information
6. **Fallback**: If Gemini fails or is unavailable, falls back to Tesseract OCR with regex parsing

## Accuracy

- **Gemini Vision API**: Excellent accuracy on handwriting and varied fonts/layouts
- **Smarty Address Verification**: USPS-certified address validation ensures deliverable, standardized addresses
- **Tesseract OCR**: Good for printed text, less reliable for handwriting

For best results with handwritten mail, ensure your Gemini API key is configured. For guaranteed deliverable addresses, configure Smarty API credentials.

## Troubleshooting

### "No OCR method available"
Install dependencies: `pip install google-generativeai pillow pytesseract`

### "Warning: No Gemini API key provided"
Set your API key in `.env` or as an environment variable:
```bash
export GEMINI_API_KEY="your_key_here"
```

### "Warning: No Smarty credentials provided"
Set your Smarty credentials in `.env`:
```bash
SMARTY_AUTH_ID="your_auth_id_here"
SMARTY_AUTH_TOKEN="your_auth_token_here"
```

### Address verification shows "invalid" or "insufficient_data"
- Check that the extracted address is reasonably complete
- Smarty requires at least a street address to verify
- Some addresses may not exist in the USPS database (new construction, rural routes)
- Original extracted address is still available in the results

### Tesseract not found
Install Tesseract OCR (see Installation section above)

### Poor accuracy
- Use Gemini instead of Tesseract for handwritten mail
- Ensure image is well-lit and in focus
- Try cropping to just the return address area

## API Key Security

- Never commit your `.env` file to version control
- The `.gitignore` file is configured to exclude `.env`
- Use environment variables in production
- Regenerate API keys if accidentally exposed

## License

This project is part of the MSB-341 coursework.

## Related Projects

This tool is designed to support the Fan Mail Analysis Platform concept (see `../portfolio/projects/project-2.qmd`).
