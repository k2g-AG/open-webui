import logging

import stripe

from open_webui.env import STRIPE_SECRET_KEY, STRIPE_TRIAL_PRICE_ID, STRIPE_TRIAL_PERIOD_DAYS

stripe.api_key = STRIPE_SECRET_KEY

if not STRIPE_SECRET_KEY:
    raise RuntimeError("Missing STRIPE_SECRET_KEY")

if not STRIPE_TRIAL_PRICE_ID:
    raise RuntimeError("Missing STRIPE_TRIAL_PRICE_ID")

log = logging.getLogger(__name__)

class StripeService:
    @staticmethod
    def get_customer_by_email(email: str) -> dict | None:
        log.debug(f"Attempting to fetch Stripe customer by email: {email}")
        try:
            customers = stripe.Customer.list(email=email, limit=1).data
            if customers:
                log.info(f"Found Stripe customer {customers[0]['id']} for email: {email}")
                return customers[0]
            else:
                log.info(f"No Stripe customer found for email: {email}")
                return None
        except stripe.error.StripeError as e:
            log.error(f"Stripe API Error fetching customer by email {email}: {e.code} - {e.user_message} (param: {e.param}, http_status: {e.http_status})")
            return None
        except Exception as e:
            log.error(f"Unexpected error fetching Stripe customer by email {email}: {e}")
            return None

    @staticmethod
    def create_customer(email: str, name: str, metadata: dict) -> dict | None:
        log.debug(f"Attempting to create Stripe customer for email: {email}, name: {name}")
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata
            )
            log.info(f"Successfully created Stripe customer: {customer['id']} for email: {email}")
            return customer
        except stripe.error.StripeError as e:
            log.error(f"Stripe API Error creating customer for email {email}: {e.code} - {e.user_message} (param: {e.param}, http_status: {e.http_status})")
            return None
        except Exception as e:
            log.error(f"Unexpected error creating Stripe customer for email {email}: {e}")
            return None

    @staticmethod
    def create_trial_subscription(customer_id: str, metadata: dict) -> dict | None:
        log.debug(f"Attempting to create trial subscription for customer ID: {customer_id}")
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": STRIPE_TRIAL_PRICE_ID}],
                trial_period_days= STRIPE_TRIAL_PERIOD_DAYS,
                metadata = metadata,
                cancel_at_period_end=True
            )
            log.info(f"Successfully created trial subscription {subscription['id']} for customer: {customer_id}")
            return subscription
        except stripe.error.StripeError as e:
            log.error(f"Stripe API Error creating trial subscription for customer {customer_id}: {e.code} - {e.user_message} (param: {e.param}, http_status: {e.http_status})")
            return None
        except Exception as e:
            log.error(f"Unexpected error creating trial subscription for customer {customer_id}: {e}")
            return None

    @staticmethod
    def create_checkout_session(
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str
    ) -> dict | None:
        log.debug(f"Attempting to create checkout session for customer ID: {customer_id}")
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
                allow_promotion_codes=True,
            )
            log.info(f"Successfully created checkout session {session['id']} for customer: {customer_id}")
            return session
        except stripe.error.StripeError as e:
            log.error(f"Stripe API Error creating checkout session for customer {customer_id}: {e.code} - {e.user_message} (param: {e.param}, http_status: {e.http_status})")
            return None
        except Exception as e:
            log.error(f"Unexpected error creating checkout session for customer {customer_id}: {e}")
            return None