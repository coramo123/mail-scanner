# Mail Scanner

A Python tool that scans photos of mail (envelopes, postcards, packages) to extract return address information and sender names. Uses Google Gemini Vision API for accurate text extraction from handwriting and varied fonts, with Tesseract OCR as a fallback option.

## Features

- **Gemini Vision API Integration**: Leverages AI to accurately read handwriting and inconsistent fonts
- **Multi-format Support**: Handles envelopes, postcards, and packages with varying layouts
- **Tesseract Fallback**: Works offline with Tesseract OCR when Gemini is unavailable
- **Structured Output**: Returns sender name, street, city, state, and ZIP code
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

### 3. Configure API Key

Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

Create a `.env` file:
```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```
GEMINI_API_KEY=your_actual_api_key_here
```

## Usage

### Command Line

```bash
python mail_scanner.py path/to/mail_photo.jpg
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
```

### Python Code

```python
from mail_scanner import MailScanner
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create scanner
scanner = MailScanner()

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
    'sender_name': 'John Smith',           # or None if not found
    'street': '123 Main Street',           # or None if not found
    'city': 'Springfield',                 # or None if not found
    'state': 'IL',                         # or None if not found
    'zip': '62701',                        # or None if not found
    'full_address': '123 Main Street, Springfield, IL, 62701',
    'method': 'gemini'                     # 'gemini' or 'tesseract'
}
```

## Advanced Usage

### Force Tesseract OCR

```python
# Use Tesseract instead of Gemini (for offline use)
scanner = MailScanner(use_gemini=False)
result = scanner.scan_mail("mail.jpg")
```

### Explicit API Key

```python
# Pass API key directly instead of using .env
scanner = MailScanner(gemini_api_key="your_api_key_here")
```

### Batch Processing

```python
scanner = MailScanner()

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
4. **Fallback**: If Gemini fails or is unavailable, falls back to Tesseract OCR with regex parsing

## Accuracy

- **Gemini Vision API**: Excellent accuracy on handwriting and varied fonts/layouts
- **Tesseract OCR**: Good for printed text, less reliable for handwriting

For best results with handwritten mail, ensure your Gemini API key is configured.

## Troubleshooting

### "No OCR method available"
Install dependencies: `pip install google-generativeai pillow pytesseract`

### "Warning: No Gemini API key provided"
Set your API key in `.env` or as an environment variable:
```bash
export GEMINI_API_KEY="your_key_here"
```

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
