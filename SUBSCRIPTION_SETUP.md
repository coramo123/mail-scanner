# Subscription & Payment Setup Guide

This guide explains how to set up the subscription system with Stripe for your Mail Scanner application.

## Overview

The application now has a complete subscription management system with three tiers:
- **Free**: 10 scans/month, basic features
- **Pro**: 100 scans/month, $9.99/month, full features including address verification
- **Business**: Unlimited scans, $29.99/month, priority support + advanced features

## Prerequisites

1. A Stripe account (sign up at https://stripe.com)
2. Supabase database access
3. Running Mail Scanner application

## Step 1: Database Setup

Run the subscription schema SQL in your Supabase SQL Editor:

```bash
# Navigate to: https://supabase.com/dashboard/project/YOUR_PROJECT/sql
# Copy and run the contents of: supabase_subscriptions_schema.sql
```

This creates:
- `user_subscriptions` table
- RLS policies for security
- Helper functions for scan limits
- Automatic subscription tracking

## Step 2: Stripe Account Setup

### 2.1 Get API Keys

1. Log in to Stripe Dashboard: https://dashboard.stripe.com
2. Switch to **Test mode** (toggle in top right)
3. Navigate to: **Developers** → **API keys**
4. Copy:
   - **Publishable key** (starts with `pk_test_`)
   - **Secret key** (starts with `sk_test_`)

### 2.2 Create Products and Prices

#### Create Pro Plan:
1. Go to: **Product catalog** → **Add product**
2. Fill in:
   - Name: `Mail Scanner Pro`
   - Description: `100 scans per month with full features`
   - Pricing: `$9.99 USD` - `Recurring` - `Monthly`
3. Click **Save product**
4. Copy the **Price ID** (starts with `price_`)

#### Create Business Plan:
1. Go to: **Product catalog** → **Add product**
2. Fill in:
   - Name: `Mail Scanner Business`
   - Description: `Unlimited scans with priority support`
   - Pricing: `$29.99 USD` - `Recurring` - `Monthly`
3. Click **Save product**
4. Copy the **Price ID** (starts with `price_`)

### 2.3 Get Webhook Secret

1. Go to: **Developers** → **Webhooks**
2. Click **Add endpoint**
3. Endpoint URL: `https://your-domain.com/stripe-webhook`
   - For ngrok: `https://your-ngrok-url.ngrok-free.dev/stripe-webhook`
4. Select events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
5. Click **Add endpoint**
6. Copy the **Signing secret** (starts with `whsec_`)

## Step 3: Configure Environment Variables

Add these to your `.env` file:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Stripe Price IDs
STRIPE_PRO_PRICE_ID=price_your_pro_price_id_here
STRIPE_BUSINESS_PRICE_ID=price_your_business_price_id_here
```

## Step 4: Test the Integration

### 4.1 Start the Application

```bash
cd 401-prototype
python3 app.py
```

### 4.2 Navigate to Account Page

1. Open your app: `http://localhost:5001` (or your ngrok URL)
2. Log in
3. Click **Account & Billing** in the header

### 4.3 Test Upgrade Flow

1. Click **Upgrade to Pro** or **Upgrade to Business**
2. You'll be redirected to Stripe Checkout
3. Use Stripe test card: `4242 4242 4242 4242`
   - Expiry: Any future date
   - CVC: Any 3 digits
   - ZIP: Any 5 digits
4. Complete payment
5. You'll be redirected back with success message
6. Your subscription should now show the new plan

### 4.4 Test Scan Limits

**Free Tier:**
1. Try uploading more than 10 scans in a month
2. You should see an error message about reaching your limit
3. Error will include upgrade prompt

**Pro/Business Tier:**
1. Upgrade to Pro or Business
2. Scan limits will be increased
3. Monitor usage on Account page

## Step 5: Going Live

When ready for production:

### 5.1 Switch to Live Mode in Stripe

1. In Stripe Dashboard, toggle from **Test mode** to **Live mode**
2. Get new API keys from **Developers** → **API keys**
3. Create new products/prices for live mode
4. Set up live webhook endpoint

### 5.2 Update Environment Variables

Replace test keys with live keys:

```bash
STRIPE_SECRET_KEY=sk_live_your_live_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_live_webhook_secret
STRIPE_PRO_PRICE_ID=price_your_live_pro_price_id
STRIPE_BUSINESS_PRICE_ID=price_your_live_business_price_id
```

### 5.3 Set Up Monthly Reset

Use a cron job or scheduled task to reset monthly scans:

```sql
-- Run this on the 1st of each month
SELECT reset_monthly_scans();
```

Or use Supabase Edge Functions with pg_cron:

```sql
-- Schedule monthly reset
SELECT cron.schedule(
  'reset-monthly-scans',
  '0 0 1 * *',  -- First day of month at midnight
  'SELECT reset_monthly_scans()'
);
```

## Features Implemented

### User-Facing Features:
✅ Subscription overview with current plan
✅ Usage tracking with progress bar
✅ Three-tier pricing plans (Free, Pro, Business)
✅ Stripe Checkout integration
✅ Customer Portal for billing management
✅ Scan history with statistics
✅ Upgrade/downgrade functionality
✅ Scan limit enforcement

### Backend Features:
✅ Supabase subscription management
✅ Stripe webhook handling
✅ Automatic scan count tracking
✅ Plan limit enforcement
✅ RLS security policies
✅ Session-based authentication

### Admin Features:
✅ Subscription status tracking
✅ Payment history (via Stripe Dashboard)
✅ Usage analytics
✅ Automated billing

## Troubleshooting

### "Plan not configured" Error
- Make sure `STRIPE_PRO_PRICE_ID` and `STRIPE_BUSINESS_PRICE_ID` are set in `.env`
- Verify the price IDs are correct from Stripe Dashboard

### Webhook Not Working
- Check the webhook URL is correct and accessible
- Verify webhook secret matches in `.env`
- Test webhook with Stripe CLI: `stripe listen --forward-to localhost:5001/stripe-webhook`

### Scan Limit Not Enforcing
- Verify `user_subscriptions` table exists
- Check RLS policies are enabled
- Run `SELECT can_user_scan('user-id-here')` in Supabase SQL editor

### Payment Successful But Plan Not Updated
- Check webhook is receiving events
- Review app logs for webhook processing
- Verify webhook signature is valid

## Support

For issues:
1. Check app logs
2. Review Stripe Dashboard → Events for webhook delivery
3. Verify database functions are working
4. Test with Stripe test cards

## Test Cards

Use these for testing:

| Card Number | Description |
|-------------|-------------|
| 4242 4242 4242 4242 | Success |
| 4000 0000 0000 0002 | Declined |
| 4000 0000 0000 9995 | Insufficient funds |
| 4000 0000 0000 0341 | Requires authentication |

## Next Steps

1. ✅ Run the database schema
2. ✅ Set up Stripe products
3. ✅ Configure environment variables
4. ✅ Test the payment flow
5. ✅ Monitor usage and limits
6. ⬜ Set up monthly reset automation
7. ⬜ Switch to live mode for production

Your subscription system is now ready to use!
