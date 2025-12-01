"""
Stripe Payment Integration for Mail Scanner
Handles subscriptions, payments, and webhooks
"""

import os
import stripe
from dotenv import load_dotenv

load_dotenv()

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Plan configurations
PLANS = {
    'free': {
        'name': 'Free Trial',
        'price': 0,
        'scan_limit': 100,
        'features': [
            '100 scans per month',
            'Photo uploads',
            'Mobile camera scanning',
            'Full sender extraction',
            'Export to CSV/Excel',
            'Email support'
        ],
        'stripe_price_id': None
    },
    'starter': {
        'name': 'Starter',
        'price': 199,
        'scan_limit': 1000,
        'features': [
            '1,000 scans per month',
            'Photo uploads',
            'Mobile camera scanning',
            'Full sender extraction',
            'Address verification (USPS)',
            'Export to CSV/Excel',
            'Advanced categorization',
            'Email support'
        ],
        'stripe_price_id': os.getenv('STRIPE_STARTER_PRICE_ID')
    },
    'growth': {
        'name': 'Growth',
        'price': 349,
        'scan_limit': 3000,
        'features': [
            '3,000 scans per month',
            'Photo uploads',
            'Mobile camera scanning',
            'Full sender extraction',
            'Address verification (USPS)',
            'Export to CSV/Excel',
            'Advanced categorization',
            'Email support'
        ],
        'stripe_price_id': os.getenv('STRIPE_GROWTH_PRICE_ID')
    },
    'scale': {
        'name': 'Scale',
        'price': 499,
        'scan_limit': 10000,
        'features': [
            '10,000 scans per month',
            'Photo uploads',
            'Mobile camera scanning',
            'Full sender extraction',
            'Address verification (USPS)',
            'Export to CSV/Excel',
            'Advanced categorization',
            'Email support'
        ],
        'stripe_price_id': os.getenv('STRIPE_SCALE_PRICE_ID')
    },
    'enterprise': {
        'name': 'Enterprise',
        'price': None,  # Custom pricing
        'scan_limit': 999999,  # Effectively unlimited
        'features': [
            '10,000+ scans per month',
            'Photo uploads',
            'Mobile camera scanning',
            'Full sender extraction',
            'Address verification (USPS)',
            'Export to CSV/Excel',
            'Advanced categorization',
            'Email support'
        ],
        'stripe_price_id': None  # Contact sales
    }
}


def create_customer(email, user_id):
    """
    Create a Stripe customer

    Args:
        email: Customer email
        user_id: User ID from database

    Returns:
        Stripe Customer object
    """
    try:
        customer = stripe.Customer.create(
            email=email,
            metadata={'user_id': str(user_id)}
        )
        return customer
    except stripe.error.StripeError as e:
        print(f"Error creating Stripe customer: {e}")
        raise


def create_checkout_session(customer_id, price_id, success_url, cancel_url):
    """
    Create a Stripe Checkout session for subscription

    Args:
        customer_id: Stripe customer ID
        price_id: Stripe price ID for the plan
        success_url: URL to redirect on success
        cancel_url: URL to redirect on cancellation

    Returns:
        Checkout session object
    """
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            subscription_data={
                'trial_period_days': 0,  # No trial for now
            }
        )
        return session
    except stripe.error.StripeError as e:
        print(f"Error creating checkout session: {e}")
        raise


def get_subscription(subscription_id):
    """
    Get subscription details from Stripe

    Args:
        subscription_id: Stripe subscription ID

    Returns:
        Subscription object
    """
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        return subscription
    except stripe.error.StripeError as e:
        print(f"Error retrieving subscription: {e}")
        raise


def cancel_subscription(subscription_id, at_period_end=True):
    """
    Cancel a Stripe subscription

    Args:
        subscription_id: Stripe subscription ID
        at_period_end: If True, cancel at end of billing period. If False, cancel immediately.

    Returns:
        Updated subscription object
    """
    try:
        if at_period_end:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
        else:
            subscription = stripe.Subscription.delete(subscription_id)
        return subscription
    except stripe.error.StripeError as e:
        print(f"Error cancelling subscription: {e}")
        raise


def update_subscription(subscription_id, new_price_id):
    """
    Update (upgrade/downgrade) a subscription

    Args:
        subscription_id: Stripe subscription ID
        new_price_id: New Stripe price ID

    Returns:
        Updated subscription object
    """
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)

        # Update the subscription with new price
        updated_subscription = stripe.Subscription.modify(
            subscription_id,
            items=[{
                'id': subscription['items']['data'][0].id,
                'price': new_price_id,
            }],
            proration_behavior='create_prorations'
        )
        return updated_subscription
    except stripe.error.StripeError as e:
        print(f"Error updating subscription: {e}")
        raise


def construct_webhook_event(payload, sig_header):
    """
    Verify and construct a webhook event from Stripe

    Args:
        payload: Request body
        sig_header: Stripe signature header

    Returns:
        Verified event object
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
        return event
    except ValueError as e:
        print(f"Invalid payload: {e}")
        raise
    except stripe.error.SignatureVerificationError as e:
        print(f"Invalid signature: {e}")
        raise


def get_plan_info(plan_type):
    """
    Get plan information by plan type

    Args:
        plan_type: 'free', 'pro', or 'business'

    Returns:
        Plan configuration dict
    """
    return PLANS.get(plan_type, PLANS['free'])


def get_all_plans():
    """
    Get all available plans

    Returns:
        Dictionary of all plans
    """
    return PLANS


def create_customer_portal_session(customer_id, return_url):
    """
    Create a Stripe Customer Portal session for managing subscriptions

    Args:
        customer_id: Stripe customer ID
        return_url: URL to return to after portal session

    Returns:
        Portal session object
    """
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session
    except stripe.error.StripeError as e:
        print(f"Error creating portal session: {e}")
        raise
