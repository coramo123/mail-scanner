# Deploying Mail Scanner to Render (Free Tier)

This guide will help you deploy your Mail Scanner app to Render's free tier.

## Prerequisites

1. A GitHub account
2. Your project pushed to a GitHub repository
3. Your API keys ready:
   - Gemini API Key
   - Smarty Auth ID and Token
   - Supabase URL and Key

## Step 1: Push to GitHub

If you haven't already, push your project to GitHub:

```bash
cd 401-prototype
git init
git add .
git commit -m "Initial commit - Mail Scanner app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

## Step 2: Sign Up for Render

1. Go to [Render.com](https://render.com)
2. Click "Get Started for Free"
3. Sign up with your GitHub account (recommended for easy deployment)

## Step 3: Create a New Web Service

1. From your Render dashboard, click "New +"
2. Select "Web Service"
3. Connect your GitHub repository:
   - Click "Connect Account" if needed
   - Find and select your repository
   - Click "Connect"

## Step 4: Configure Your Service

Render will auto-detect your Python app. Configure the following:

**Basic Settings:**
- Name: `mail-scanner-app` (or your preferred name)
- Region: Choose closest to you
- Branch: `main`
- Runtime: `Python 3`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

**Instance Type:**
- Select: `Free` (This is the free tier!)

## Step 5: Add Environment Variables

Click "Advanced" and add these environment variables:

| Key | Value | Notes |
|-----|-------|-------|
| `SECRET_KEY` | (Auto-generated) | Click "Generate" button |
| `GEMINI_API_KEY` | Your Gemini API key | From Google AI Studio |
| `SMARTY_AUTH_ID` | Your Smarty Auth ID | From Smarty dashboard |
| `SMARTY_AUTH_TOKEN` | Your Smarty Auth Token | From Smarty dashboard |
| `SUPABASE_URL` | Your Supabase URL | From Supabase project settings |
| `SUPABASE_KEY` | Your Supabase anon key | From Supabase project settings |

**Important:** Make sure you're using your Supabase project URL and anon/public key, not the service role key.

## Step 6: Deploy

1. Click "Create Web Service"
2. Render will:
   - Clone your repository
   - Install dependencies
   - Start your app
   - This takes 2-5 minutes

3. Watch the build logs to see progress

## Step 7: Access Your App

Once deployment completes:
- Your app URL will be: `https://mail-scanner-app.onrender.com` (or your chosen name)
- Click the URL to open your deployed app
- You should see the login page

## Step 8: Update Supabase Settings

If you're using email confirmations in Supabase:

1. Go to your Supabase project
2. Navigate to Authentication > URL Configuration
3. Add your Render URL to "Site URL": `https://your-app-name.onrender.com`
4. Add to "Redirect URLs": `https://your-app-name.onrender.com/**`

## Important Notes About Free Tier

**Free Tier Limitations:**
- App spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds to wake up
- 750 hours/month (enough for one always-on app)
- 512 MB RAM

**Tips:**
- Your app URL will be `https://your-app-name.onrender.com`
- HTTPS is automatic and free
- You can add a custom domain later

## Troubleshooting

### Build Fails
- Check that all dependencies are in `requirements.txt`
- View build logs for specific errors
- Make sure Python version is compatible

### App Won't Start
- Check environment variables are set correctly
- View application logs in Render dashboard
- Verify Supabase credentials are correct

### Database Connection Issues
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Check Supabase project is active
- Make sure you're using the anon key, not service role key

### Slow First Load
- This is normal for free tier after inactivity
- App spins down after 15 minutes
- Takes ~30 seconds to wake up

## Making Updates

After initial deployment, updates are automatic:

1. Make changes to your code
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update feature"
   git push
   ```
3. Render automatically detects the push and redeploys

## Monitoring Your App

- View logs: Render Dashboard > Your Service > Logs
- Check status: Green = running, Yellow = deploying
- Monitor bandwidth and hours used in dashboard

## Cost Summary

**Monthly costs: $0**
- Web Service: Free tier
- Gemini API: Free tier (500 requests/day)
- Smarty API: Free tier (250 lookups/month)
- Supabase: Free tier (500MB database, 2GB bandwidth)

Perfect for class projects and prototypes!

## Next Steps

- Share your app URL with classmates
- Monitor usage in Render dashboard
- Consider upgrading if you need faster wake times
- Add custom domain (free on any tier)

## Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- Your app logs: Render Dashboard > Logs
