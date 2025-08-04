from dotenv import load_dotenv
load_dotenv()

import stripe
import logging
import os

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_TRIAL_PRICE_ID = os.getenv("STRIPE_TRIAL_PRICE_ID", "")
STRIPE_TRIAL_PERIOD_DAYS = os.getenv("STRIPE_TRIAL_PERIOD_DAYS", "")

stripe.api_key = STRIPE_SECRET_KEY

if not STRIPE_SECRET_KEY:
    raise RuntimeError("Missing STRIPE_SECRET_KEY")

if not STRIPE_TRIAL_PRICE_ID:
    raise RuntimeError("Missing STRIPE_TRIAL_PRICE_ID")

log = logging.getLogger(__name__)

class StripeService:
    @staticmethod
    def get_customer_by_email(email: str) -> dict | None:
        try:
            customers = stripe.Customer.list(email=email, limit=1).data
            return customers[0] if customers else None
        except Exception as e:
            log.error(f"Error fetching Stripe customer by email {email}: {e}")
            return None

    @staticmethod
    def create_customer(email: str, name: str, metadata: dict) -> dict | None:
        try:
            return stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata
            )
        except Exception as e:
            log.error(f"Error creating Stripe customer: {e}")
            return None

    @staticmethod
    def create_trial_subscription(customer_id: str) -> dict | None:
        try:
            return stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": STRIPE_TRIAL_PRICE_ID}],
                trial_period_days= STRIPE_TRIAL_PERIOD_DAYS
            )
        except Exception as e:
            log.error(f"Error creating trial subscription for customer {customer_id}: {e}")
            return None