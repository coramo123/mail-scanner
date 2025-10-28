# Mail Scanner Web Application

A beautiful web interface for scanning mail photos and exporting sender information to spreadsheets.

## Features

- **Drag & Drop Upload**: Upload multiple mail photos at once
- **Batch Processing**: Scan multiple photos in one go
- **Smart Name Detection**: Finds sender names from return addresses, signatures, or letter content
- **Address Extraction**: Automatically extracts street, city, state, and ZIP
- **Spreadsheet Export**: Export results to CSV or Excel
- **Session Management**: Results persist during your session
- **Beautiful UI**: Modern, responsive design that works on all devices

## Installation

### 1. Install Dependencies

```bash
cd /Users/coramontgomery/Desktop/MSB-341/401-prototype
pip install -r requirements.txt
```

### 2. Ensure API Key is Configured

Your Gemini API key should already be in the `.env` file:

```bash
# Check that .env exists and has your API key
cat .env
```

## Running the Web App

Start the server:

```bash
python3 app.py
```

You should see:

```
============================================================
MAIL SCANNER WEB APP
============================================================
Starting server at http://localhost:5000
Press Ctrl+C to stop
============================================================
```

Then open your browser and go to:
```
http://localhost:5000
```

## How to Use

### 1. Upload Photos

**Option A: Drag & Drop**
- Drag mail photos directly into the upload area
- The area will highlight when you hover over it

**Option B: Click to Browse**
- Click the upload area
- Select one or multiple mail photos
- Supports: JPG, PNG, WEBP, GIF (max 16MB per file)

### 2. Scan Photos

- Click the "Scan Selected Photos" button
- Wait for the progress bar to complete
- Results will appear in the table below

### 3. View Results

The results table shows:
- **File**: Original filename
- **Sender Name**: Extracted from return address or signature
- **Street**: Street address
- **City**: City name
- **State**: State abbreviation or full name
- **ZIP**: ZIP code
- **Actions**: Delete individual results

### 4. Export to Spreadsheet

**CSV Export**
- Click "Export to CSV" button
- Opens in Excel, Google Sheets, or any spreadsheet app

**Excel Export**
- Click "Export to Excel" button
- Creates a formatted .xlsx file

Both exports include:
- Filename
- Sender Name
- Street
- City
- State
- ZIP
- Full Address
- Upload Timestamp

### 5. Manage Results

**Delete Individual Result**
- Click the "Delete" button next to any result

**Clear All Results**
- Click the "Clear All" button
- Confirms before deleting everything

## Features in Detail

### Smart Name Detection

The scanner looks for sender names in multiple places:
1. Return address (top-left of envelope)
2. Signature at bottom of letter
3. Closing statement ("Sincerely, [Name]")
4. Letterhead
5. "From:" lines

### Batch Processing

Upload multiple photos at once:
- All photos are processed in a single batch
- Progress bar shows overall progress
- Results appear immediately after scanning

### Session Persistence

Your results are saved during your browser session:
- Refresh the page without losing data
- Results persist until you clear them or close the browser
- Each browser session has its own set of results

## File Structure

```
401-prototype/
├── app.py                      # Flask web application
├── mail_scanner.py             # Core scanning logic
├── templates/
│   └── index.html             # Web interface
├── static/
│   └── css/
│       └── style.css          # Styling
├── uploads/                   # Uploaded images (auto-created)
├── exports/                   # Generated spreadsheets (auto-created)
├── .env                       # API key (keep secret!)
└── requirements.txt           # Dependencies
```

## Troubleshooting

### Port Already in Use

If port 5000 is already in use, edit `app.py` line 241:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port
```

### Upload Fails

- Check file size (max 16MB per file)
- Ensure file is an image (JPG, PNG, WEBP, GIF)
- Check that uploads folder exists and is writable

### Export Fails

- Ensure you have scanned at least one photo
- Check that exports folder exists and is writable
- Verify pandas and openpyxl are installed

### API Rate Limits

Gemini has free tier limits:
- 1,000 requests per month
- If you hit the limit, wait until next month or upgrade your plan

## Security Notes

- Never commit your `.env` file to version control
- The `.gitignore` file protects your API key
- In production, set a strong `SECRET_KEY` environment variable
- Uploaded images are stored temporarily and can be deleted manually

## Advanced Usage

### Run on Different Host/Port

```bash
# Edit app.py, line 241
app.run(debug=True, host='127.0.0.1', port=8080)
```

### Production Deployment

For production, use a proper WSGI server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Clear Uploaded Files

```bash
rm -rf uploads/*
rm -rf exports/*
```

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **OCR**: Google Gemini Vision API
- **Export**: Pandas (CSV/Excel)
- **Styling**: Custom CSS with gradient design

## Support

For issues or questions:
1. Check that all dependencies are installed
2. Verify your Gemini API key is configured
3. Check the terminal for error messages
4. Review the README for troubleshooting tips

Enjoy scanning your mail!
