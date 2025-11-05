# Supabase Setup Guide

This guide will walk you through setting up Supabase for user authentication and database storage in the Mail Scanner app.

## Step 1: Create a Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up or log in to your account
3. Click "New Project"
4. Fill in the project details:
   - **Name**: Mail Scanner (or whatever you prefer)
   - **Database Password**: Choose a strong password (save this!)
   - **Region**: Choose the closest region to your location
   - **Pricing Plan**: Free tier is fine for development
5. Click "Create new project"
6. Wait for the project to finish setting up (takes 1-2 minutes)

## Step 2: Get Your API Credentials

1. Once your project is ready, go to **Project Settings** (gear icon in sidebar)
2. Navigate to **API** section
3. You'll need two values:
   - **Project URL** (looks like: `https://xxxxxxxxxxxxx.supabase.co`)
   - **anon public** key (a long string starting with `eyJ...`)
4. Copy these values - you'll add them to your `.env` file

## Step 3: Set Up the Database Schema

1. In your Supabase dashboard, click **SQL Editor** in the left sidebar
2. Click **New query**
3. Open the `supabase_schema.sql` file in this project directory
4. Copy the entire contents of that file
5. Paste it into the Supabase SQL Editor
6. Click **Run** (or press Cmd/Ctrl + Enter)
7. You should see "Success. No rows returned" - this means the tables were created successfully

## Step 4: Configure Authentication

1. In your Supabase dashboard, go to **Authentication** in the left sidebar
2. Click on **Providers**
3. Make sure **Email** is enabled (it should be by default)
4. Optional: Configure other providers like Google, GitHub, etc.
5. Go to **Email Templates** to customize the emails sent to users (optional)

## Step 5: Update Your .env File

1. In your project directory, make sure you have a `.env` file:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and add your Supabase credentials:
   ```
   SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
   SUPABASE_KEY=eyJxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

3. Also set a secure SECRET_KEY for Flask sessions:
   ```
   SECRET_KEY=your_random_secret_key_here
   ```
   (Generate a random string, or use: `python3 -c "import secrets; print(secrets.token_hex(32))"`)

## Step 6: Verify the Setup

1. In Supabase dashboard, go to **Table Editor**
2. You should see a table called `scan_results`
3. It should have columns like: id, user_id, filename, sender_name, street, city, state, etc.

## Step 7: Test Authentication (After Code Integration)

After we integrate the authentication code:

1. Start your Flask app
2. Navigate to the signup page
3. Create a test account
4. Check your Supabase dashboard under **Authentication > Users** to see the new user
5. Upload and scan some mail
6. Check **Table Editor > scan_results** to see the stored data

## Security Notes

- **Never commit your `.env` file** to version control (it's already in `.gitignore`)
- The **anon key** is safe to use in client-side code - it's public
- Row Level Security (RLS) ensures users can only access their own data
- For production, consider:
  - Enabling email confirmation
  - Adding rate limiting
  - Using a custom domain
  - Upgrading to a paid plan for better performance

## Useful Supabase Dashboard Links

- **Table Editor**: View and edit data in your tables
- **SQL Editor**: Run custom SQL queries
- **Authentication**: Manage users and auth settings
- **API Docs**: Auto-generated API documentation for your project
- **Logs**: View database and API logs

## Troubleshooting

### "relation does not exist" error
- Make sure you ran the `supabase_schema.sql` file in the SQL Editor
- Check that you're connected to the correct project

### Users can't see their data
- Verify Row Level Security policies are set up correctly
- Check that the user is properly authenticated
- Look at Supabase Logs for any policy violations

### Authentication not working
- Verify your SUPABASE_URL and SUPABASE_KEY are correct in `.env`
- Make sure Email authentication is enabled in Supabase dashboard
- Check that you restarted your Flask app after updating `.env`

## Next Steps

Once this setup is complete, the Mail Scanner app will:
- Allow users to sign up and log in
- Store scan results in the database (not local JSON files)
- Show each user only their own scan results
- Support multiple users simultaneously
