# Stripe Setup Guide - Mail Scanner Subscription Plans

This guide walks you through setting up Stripe payment integration for your Mail Scanner application with the new pricing structure.

## Pricing Structure

| Plan | Price/Month | Usage Limit | Features |
|------|-------------|-------------|----------|
| **Free Trial** | $0 | 10 scans | Basic features to try it out |
| **Starter** | $199 | 1,000 scans | Full features + USPS verification |
| **Growth** | $349 | 3,000 scans | Everything in Starter + priority support |
| **Scale** | $499 | 10,000 scans | Everything in Growth + API access |
| **Enterprise** | Custom | 10,000+ scans | Everything + dedicated support |

## Step 1: Create Stripe Account

1. Go to https://stripe.com
2. Sign up for a free account
3. Switch to **Test mode** (toggle in top right)

## Step 2: Create Products and Prices

### Create Starter Plan ($199/month)

1. Go to **Product catalog** → **Add product**
2. Fill in:
   - **Name**: `Mail Scanner - Starter`
   - **Description**: `1,000 scans per month with full features`
   - **Pricing**:
     - Amount: `$199.00 USD`
     - Billing period: `Monthly`
     - Model: `Recurring`
3. Click **Save product**
4. **Copy the Price ID** (starts with `price_`) - you'll need this for `STRIPE_STARTER_PRICE_ID`

### Create Growth Plan ($349/month)

1. Go to **Product catalog** → **Add product**
2. Fill in:
   - **Name**: `Mail Scanner - Growth`
   - **Description**: `3,000 scans per month with priority support`
   - **Pricing**:
     - Amount: `$349.00 USD`
     - Billing period: `Monthly`
     - Model: `Recurring`
3. Click **Save product**
4. **Copy the Price ID** - you'll need this for `STRIPE_GROWTH_PRICE_ID`

### Create Scale Plan ($499/month)

1. Go to **Product catalog** → **Add product**
2. Fill in:
   - **Name**: `Mail Scanner - Scale`
   - **Description**: `10,000 scans per month with API access`
   - **Pricing**:
     - Amount: `$499.00 USD`
     - Billing period: `Monthly`
     - Model: `Recurring`
3. Click **Save product**
4. **Copy the Price ID** - you'll need this for `STRIPE_SCALE_PRICE_ID`

**Note:** Enterprise plan doesn't need a Stripe product since it uses custom pricing and requires contacting sales.

## Step 3: Get API Keys

1. Go to **Developers** → **API keys**
2. Copy your keys:
   - **Publishable key** (starts with `pk_test_`)
   - **Secret key** (starts with `sk_test_`) - Click "Reveal test key"

## Step 4: Set Up Webhook

1. Go to **Developers** → **Webhooks**
2. Click **Add endpoint**
3. **Endpoint URL**:
   - For ngrok: `https://your-ngrok-url.ngrok-free.dev/stripe-webhook`
   - For production: `https://yourdomain.com/stripe-webhook`
4. **Select events to listen for:**
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
5. Click **Add endpoint**
6. **Copy the Signing secret** (starts with `whsec_`)

## Step 5: Update .env File

Add these environment variables to your `.env` file:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_YOUR_SECRET_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_PUBLISHABLE_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE

# Stripe Price IDs
STRIPE_STARTER_PRICE_ID=price_YOUR_STARTER_PRICE_ID
STRIPE_GROWTH_PRICE_ID=price_YOUR_GROWTH_PRICE_ID
STRIPE_SCALE_PRICE_ID=price_YOUR_SCALE_PRICE_ID
```

## Step 6: Run Database Migration

Run the updated subscription schema in your Supabase SQL Editor:

```sql
-- Navigate to: https://supabase.com/dashboard/project/YOUR_PROJECT/sql
-- Copy and execute: supabase_subscriptions_schema.sql
```

This updates the plan types to support the new tiers.

## Step 7: Test Payment Flow

### Test with Stripe Test Cards

Use these test cards in Stripe Checkout:

| Card Number | Scenario |
|-------------|----------|
| 4242 4242 4242 4242 | Successful payment |
| 4000 0000 0000 0002 | Card declined |
| 4000 0000 0000 9995 | Insufficient funds |
| 4000 0000 0000 0341 | Requires authentication (3D Secure) |

**Test Details:**
- **Expiry**: Any future date (e.g., 12/34)
- **CVC**: Any 3 digits (e.g., 123)
- **ZIP**: Any 5 digits (e.g., 12345)

### Testing Steps

1. **Access your app**:
   - HTTPS: https://your-ngrok-url.ngrok-free.dev
   - HTTP: http://your-local-ip:5001

2. **Log in and go to Account page**

3. **Try upgrading to Starter plan**:
   - Click "Upgrade to Starter"
   - Enter test card: 4242 4242 4242 4242
   - Complete checkout
   - Verify redirect to success page

4. **Check subscription updated**:
   - View current plan shows "Starter"
   - Usage shows "0 of 1,000 scans used"
   - Price shows "$199/month"

5. **Test scan limits**:
   - Upload and scan items
   - Watch usage counter increment
   - Try exceeding limit (if on Free plan with 10 scans)

6. **Test plan switching**:
   - Click "Switch to Growth"
   - Complete checkout with test card
   - Verify plan updated to Growth
   - Check limit updated to 3,000 scans

## Step 8: Monitor & Debug

### View Stripe Events

1. Go to **Developers** → **Events**
2. See all webhook events and their status
3. Click any event to see payload and response

### Check Webhook Deliveries

1. Go to **Developers** → **Webhooks**
2. Click your webhook endpoint
3. View delivery attempts and responses
4. Use "Send test webhook" to test manually

### Common Issues

**"Plan not configured" error:**
- Verify all three price IDs are in your `.env` file
- Restart your Flask app after updating `.env`
- Check price IDs match exactly from Stripe Dashboard

**Webhook not receiving events:**
- Ensure webhook URL is accessible (test with curl)
- Verify webhook secret matches in `.env`
- Check ngrok isn't blocking requests
- Look for errors in Flask app logs

**Payment succeeds but plan doesn't update:**
- Check webhook is receiving events
- Review Flask app logs for errors
- Verify database functions are working
- Check Stripe event shows correct price ID

## Going Live

When ready for production:

### 1. Switch to Live Mode

1. In Stripe Dashboard, toggle from **Test mode** to **Live mode**
2. Get new live API keys from **Developers** → **API keys**
3. Create new products/prices for live mode
4. Set up new webhook for production domain

### 2. Update Environment Variables

Replace test keys with live keys in production `.env`:

```bash
STRIPE_SECRET_KEY=sk_live_YOUR_LIVE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_LIVE_PUBLISHABLE_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_LIVE_WEBHOOK_SECRET
STRIPE_STARTER_PRICE_ID=price_YOUR_LIVE_STARTER_PRICE_ID
STRIPE_GROWTH_PRICE_ID=price_YOUR_LIVE_GROWTH_PRICE_ID
STRIPE_SCALE_PRICE_ID=price_YOUR_LIVE_SCALE_PRICE_ID
```

### 3. Set Up Monthly Reset

Create a cron job or Supabase Edge Function to reset monthly scans:

```sql
-- Schedule this to run on the 1st of each month
SELECT reset_monthly_scans();
```

### 4. Monitor Production

- Set up Stripe email notifications for failed payments
- Monitor webhook delivery success rate
- Track customer subscription metrics
- Review monthly recurring revenue (MRR)

## Enterprise Plan Handling

The Enterprise plan works differently:

- **No Stripe checkout** - uses "Contact Sales" button
- **Sends email** to `sales@mailscanner.com`
- **Manual setup** required for custom pricing
- **Unlimited scans** (999,999 limit in database)

To set up Enterprise customers manually:
1. Create customer in Stripe Dashboard
2. Create custom subscription with negotiated price
3. Update user's subscription in Supabase to `plan_type = 'enterprise'`

## Support

For help:
- Check Stripe Dashboard → Events for webhook details
- Review Flask app logs for errors
- Test webhooks with Stripe CLI: `stripe listen --forward-to localhost:5001/stripe-webhook`
- Contact Stripe support for payment issues

## Summary

✅ Create 3 products in Stripe (Starter, Growth, Scale)
✅ Get API keys and webhook secret
✅ Add all credentials to `.env` file
✅ Run database migration
✅ Test payment flow with test cards
✅ Monitor webhooks and events
✅ Go live when ready

Your subscription system is now configured with professional pricing tiers!
