# Quick Start Guide - Mail Scanner with Supabase

## What's New

Your Mail Scanner app now supports:
- **User Authentication**: Each user has their own account
- **Cloud Database**: Scan results are stored in Supabase (not local JSON files)
- **Multi-User Support**: Multiple users can use the app simultaneously, each seeing only their own data
- **Secure Access**: Row-level security ensures data privacy

## Getting Started

### 1. Set Up Supabase (First Time Only)

Follow the detailed instructions in `SUPABASE_SETUP.md` to:
1. Create a Supabase project
2. Get your API credentials
3. Run the database schema
4. Configure your `.env` file

### 2. Update Your Environment Variables

Make sure your `.env` file has these values:

```env
# Existing API keys
GEMINI_API_KEY=your_gemini_api_key_here
SMARTY_AUTH_ID=your_smarty_auth_id_here
SMARTY_AUTH_TOKEN=your_smarty_auth_token_here

# NEW: Supabase credentials
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# NEW: Flask secret key
SECRET_KEY=your_random_secret_key_here
```

**Generate a secure SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Start the Application

```bash
python3 app.py
```

The app will start at: http://localhost:5001

### 4. Create Your Account

1. Open http://localhost:5001 in your browser
2. You'll be redirected to the login page
3. Click "Sign up" to create a new account
4. Enter your email and password (minimum 6 characters)
5. You'll be automatically logged in

**Note**: Depending on your Supabase settings, you may need to confirm your email before logging in. Check your email inbox!

### 5. Start Scanning Mail

Once logged in:
1. Upload mail photos (drag & drop or click to browse)
2. Click "Scan Photos" to process them
3. View results in the "View Spreadsheet" tab
4. Export to CSV, Excel, or PDF

## Key Changes from Previous Version

### What Changed
- **Authentication Required**: All users must sign up/login
- **Database Storage**: Results stored in Supabase instead of local JSON files
- **User Isolation**: Each user only sees their own scan results
- **Session Management**: Login sessions are maintained across browser sessions

### What Stayed the Same
- All scanning features work exactly as before
- Export functionality (CSV, Excel, PDF) unchanged
- Address verification with Smarty still works
- Upload interface is the same

## Multiple Users

You can now have multiple users:
1. Each user creates their own account
2. Each user sees only their own scanned mail
3. Data is isolated and secure
4. Multiple people can use the app at the same time

## Troubleshooting

### "Missing Supabase credentials" Error
- Make sure you've set `SUPABASE_URL` and `SUPABASE_KEY` in your `.env` file
- Restart the Flask app after updating `.env`

### Can't Log In
- Check that you've confirmed your email (check spam folder)
- Try the "Sign up" page if you haven't created an account yet
- Verify your Supabase project is running (check dashboard)

### No Results Showing
- Make sure you're logged in
- Results are user-specific - you'll only see mail you've scanned
- Check the Supabase dashboard Table Editor to verify data is being saved

### "Authentication required" Error
- Your session may have expired - try logging in again
- Clear your browser cookies and log in again
- Check that your `SECRET_KEY` is set in `.env`

## Security Best Practices

1. **Never share your `.env` file** - it contains sensitive credentials
2. **Use strong passwords** for your accounts
3. **Don't commit `.env` to git** - it's already in `.gitignore`
4. **Rotate your SECRET_KEY** if you suspect it's been compromised
5. **For production**:
   - Use a proper production database
   - Enable email confirmation in Supabase
   - Set up rate limiting
   - Use HTTPS

## Next Steps

- Invite other users to create accounts and test the multi-user functionality
- Check your Supabase dashboard to see data being saved in real-time
- Explore Supabase features like API logs, database backups, etc.
- Consider adding more features like shared workspaces or teams

## Support

If you encounter issues:
1. Check the Flask console for error messages
2. Check the Supabase dashboard Logs section
3. Review `SUPABASE_SETUP.md` for detailed setup instructions
4. Verify all environment variables are correctly set

---

Enjoy your multi-user Mail Scanner app!
