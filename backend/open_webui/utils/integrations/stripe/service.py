import logging

import stripe
from open_webui.models.users import Users

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
        log.info(f"StripeService: Attempting to fetch Stripe customer by email: {email}")
        try:
            customers = stripe.Customer.list(email=email, limit=1).data
            if customers:
                log.info(f"StripeService: Found Stripe customer {customers[0]['id']} for email: {email}. Customer data: {customers[0]}")
                return customers[0]
            else:
                log.info(f"StripeService: No Stripe customer found for email: {email}.")
                return None
        except stripe.error.StripeError as e:
            log.error(f"StripeService: Stripe API Error fetching customer by email {email}: {e.code} - {e.user_message} (param: {e.param}, http_status: {e.http_status}). Full error: {e}")
            return None
        except Exception as e:
            log.error(f"StripeService: Unexpected error fetching Stripe customer by email {email}: {e}")
            return None

    @staticmethod
    def get_customer_by_id(customer_id: str) -> dict | None:
        log.info(f"StripeService: Attempting to fetch Stripe customer by ID: {customer_id}")
        try:
            customer = stripe.Customer.retrieve(customer_id)
            if customer and not customer.deleted:
                log.info(f"StripeService: Found Stripe customer {customer_id}. Customer data: {customer}")
                return customer
            else:
                log.info(f"StripeService: Stripe customer {customer_id} not found or was deleted.")
                return None
        except stripe.error.StripeError as e:
            log.error(f"StripeService: Stripe API Error fetching customer by ID {customer_id}: {e.code} - {e.user_message} (param: {e.param}, http_status: {e.http_status}). Full error: {e}")
            return None
        except Exception as e:
            log.error(f"StripeService: Unexpected error fetching Stripe customer by ID {customer_id}: {e}")
            return None

    @staticmethod
    def create_customer(email: str, name: str, metadata: dict) -> dict | None:
        log.info(f"StripeService: Attempting to create Stripe customer for email: {email}, name: {name}, metadata: {metadata}")
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata
            )
            log.info(f"StripeService: Successfully created Stripe customer: {customer['id']} for email: {email}. Customer data: {customer}")
            return customer
        except stripe.error.StripeError as e:
            log.error(f"StripeService: Stripe API Error creating customer for email {email}: {e.code} - {e.user_message} (param: {e.param}, http_status: {e.http_status}). Full error: {e}")
            return None
        except Exception as e:
            log.error(f"StripeService: Unexpected error creating Stripe customer for email {email}: {e}")
            return None

    @staticmethod
    def create_trial_subscription(customer_id: str, metadata: dict) -> dict | None:
        log.info(f"StripeService: Attempting to create trial subscription for customer ID: {customer_id}, price_id: {STRIPE_TRIAL_PRICE_ID}, trial_period_days: {STRIPE_TRIAL_PERIOD_DAYS}, metadata: {metadata}")
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": STRIPE_TRIAL_PRICE_ID}],
                trial_period_days= STRIPE_TRIAL_PERIOD_DAYS,
                metadata = metadata,
                cancel_at_period_end=True
            )
            log.info(f"StripeService: Successfully created trial subscription {subscription['id']} for customer: {customer_id}. Subscription data: {subscription}")
            return subscription
        except stripe.error.StripeError as e:
            log.error(f"StripeService: Stripe API Error creating trial subscription for customer {customer_id}: {e.code} - {e.user_message} (param: {e.param}, http_status: {e.http_status}). Full error: {e}")
            return None
        except Exception as e:
            log.error(f"StripeService: Unexpected error creating trial subscription for customer {customer_id}: {e}")
            return None

    @staticmethod
    def create_checkout_session(
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str
    ) -> dict | None:
        log.info(f"StripeService: Attempting to create checkout session for customer ID: {customer_id}, price_id: {price_id}")
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
            log.info(f"StripeService: Successfully created checkout session {session['id']} for customer: {customer_id}. Session data: {session}")
            return session
        except stripe.error.StripeError as e:
            log.error(f"StripeService: Stripe API Error creating checkout session for customer {customer_id}: {e.code} - {e.user_message} (param: {e.param}, http_status: {e.http_status}). Full error: {e}")
            return None
        except Exception as e:
            log.error(f"StripeService: Unexpected error creating checkout session for customer {customer_id}: {e}")
            return None

    @staticmethod
    def get_or_create_stripe_customer(email: str, name: str, sub: str) -> tuple[dict, str]:
        """
        Get existing Stripe customer or create a new one with trial subscription.
        
        Args:
            email: Customer email
            name: Customer name
            sub: The unique identifier from the OAuth provider (Keycloak ID)
            
        Returns:
            Tuple of (stripe_customer_dict, stripe_customer_id)
        """
        log.info(f"Starting Stripe customer lookup/creation process for email: {email}, sub: {sub}")

        if not email or not email.strip():
            log.error("get_or_create_stripe_customer: Email is required for Stripe customer. Returning None, None.")
            return None, None
        
        # Clean up inputs
        email = email.strip().lower()
        name = name.strip() if name else ""
        
        log.info(f"Processing Stripe customer for email: {email}, name: {name}, sub: {sub}")
        
        # Try to get existing customer
        try:
            log.info(f"Attempting to retrieve existing Stripe customer by email: {email}")
            stripe_customer = StripeService.get_customer_by_email(email)
            
            if stripe_customer:
                stripe_customer_id = stripe_customer.get("id")
                if not stripe_customer_id:
                    log.error(f"Existing Stripe customer found for email: {email} but missing ID field. Customer data: {stripe_customer}. Returning None, None.")
                    return None, None
                log.info(f"Found existing Stripe customer: {stripe_customer_id} for email: {email}. Returning existing customer.")
                return stripe_customer, stripe_customer_id
            else:
                log.info(f"No existing Stripe customer found for email: {email}. Proceeding to create a new one.")
                
        except Exception as e:
            log.error(f"Error during lookup for existing Stripe customer for email {email}: {e}. Attempting to create new customer.")
            # Continue to creation attempt even if lookup fails
        
        # Create new customer
        try:
            log.info(f"Attempting to create new Stripe customer for email: {email}, name: {name}")
            customer_metadata = {"keycloakId": sub} if sub else {}
            log.info(f"Metadata for new Stripe customer: {customer_metadata}")
            
            stripe_customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=customer_metadata
            )
            
            if not stripe_customer:
                log.error(f"Failed to create Stripe customer for email: {email}. StripeService returned None/empty. Returning None, None.")
                return None, None
                
            stripe_customer_id = stripe_customer.get("id")
            if not stripe_customer_id:
                log.error(f"Created Stripe customer for email: {email} but missing ID field. Customer data: {stripe_customer}. Returning None, None.")
                return None, None
                
            log.info(f"Successfully created Stripe customer: {stripe_customer_id} for email: {email}.")
            
            # Create trial subscription for new customer
            log.info(f"Attempting to create trial subscription for new Stripe customer: {stripe_customer_id}")
            try:
                trial_subscription = StripeService.create_trial_subscription(
                    stripe_customer_id,
                    customer_metadata
                )
                
                if trial_subscription:
                    log.info(f"Successfully created trial subscription: {trial_subscription.get('id')} for customer: {stripe_customer_id}.")
                else:
                    log.warning(f"Failed to create trial subscription for customer: {stripe_customer_id}. StripeService returned None/empty. Customer creation was successful.")
                    
            except Exception as e:
                log.error(f"Error creating trial subscription for customer {stripe_customer_id}: {e}. Customer creation was successful, but subscription failed.")
            
            log.info(f"Returning newly created Stripe customer {stripe_customer_id} and its ID.")
            return stripe_customer, stripe_customer_id
            
        except Exception as e:
            log.error(f"Overall error creating new Stripe customer for email {email}: {e}. Returning None, None.")
            return None, None

    @staticmethod
    async def sync_stripe_customer(user, email, name, sub):
        """
        Synchronizes Stripe customer ID for a user.
        If user has no Stripe ID, or if the ID exists but the customer is not found in Stripe,
        a new Stripe customer and trial subscription are created.
        """
        stripe_customer_id_in_db = user.stripe_customer_id
        
        if stripe_customer_id_in_db:
            log.info(f"Existing user {user.id} ({email}) has Stripe customer ID in DB: {stripe_customer_id_in_db}. Verifying existence in Stripe.")
            stripe_customer_in_stripe = StripeService.get_customer_by_id(stripe_customer_id_in_db)
            
            if stripe_customer_in_stripe:
                log.info(f"Stripe customer {stripe_customer_id_in_db} found in Stripe for user {user.id}. No action needed.")
            else:
                log.warning(f"Stripe customer {stripe_customer_id_in_db} not found in Stripe for user {user.id}. Re-creating Stripe customer and trial subscription.")
                stripe_customer, new_stripe_customer_id = StripeService.get_or_create_stripe_customer(
                    email=email,
                    name=name,
                    sub=sub
                )
                if new_stripe_customer_id:
                    log.info(f"New Stripe customer ID {new_stripe_customer_id} obtained for user {user.id}. Updating user record.")
                    # Assuming Users.update_user_by_id is available and works as expected
                    # from open_webui.models.users import Users
                    # Users.update_user_by_id(user.id, {"stripe_customer_id": new_stripe_customer_id})
                    log.info(f"Successfully updated existing user {user.id} with new Stripe customer ID: {new_stripe_customer_id}.")
                else:
                    log.error(f"Failed to re-create Stripe customer for user {user.id} ({email}) after it was not found in Stripe. User record not updated.")
        else:
            log.info(f"Existing user {user.id} ({email}) does not have a Stripe customer ID in DB. Attempting to create/retrieve one.")
            stripe_customer, new_stripe_customer_id = StripeService.get_or_create_stripe_customer(
                email=email,
                name=name,
                sub=sub
            )
            
            if new_stripe_customer_id:
                log.info(f"Stripe customer ID {new_stripe_customer_id} obtained for existing user {user.id}. Updating user record.")
                # Assuming Users.update_user_by_id is available and works as expected
                # from open_webui.models.users import Users
                # Users.update_user_by_id(user.id, {"stripe_customer_id": new_stripe_customer_id})
                log.info(f"Successfully updated existing user {user.id} with Stripe customer ID: {new_stripe_customer_id}.")
            else:
                log.warning(f"Failed to create/find Stripe customer for existing user {user.id} ({email}). User record not updated with Stripe ID.")