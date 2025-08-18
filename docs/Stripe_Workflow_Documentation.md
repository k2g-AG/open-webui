# Stripe Integration Workflow Documentation

This document outlines the workflow for Stripe integration within the Open WebUI (OWUI) application, covering user login, account verification, subscription management, and handling of trial expirations.

## 1. User Login and Initial Stripe Account Check

When a user logs into OWUI via OAuth, the `handle_callback` function in [`backend/open_webui/utils/oauth.py`](backend/open_webui/utils/oauth.py:349) is invoked. This function is responsible for processing the OAuth token and user data.

A critical step during this process is the synchronization of the user's Stripe customer ID. This is handled by the `StripeService.sync_stripe_customer` method, called at [`backend/open_webui/utils/oauth.py`](backend/open_webui/utils/oauth.py:569).

### `StripeService.sync_stripe_customer` ([`backend/open_webui/utils/integrations/stripe/service.py`](backend/open_webui/utils/integrations/stripe/service.py:214))

This method performs the following checks and actions:

1.  **Check for existing Stripe Customer ID in DB**:
    *   It first checks if the user's record in the OWUI database (`user.stripe_customer_id`) already contains a Stripe customer ID.
2.  **Verify Stripe Customer in Stripe**:
    *   If a `stripe_customer_id` exists in the DB, it attempts to retrieve this customer from Stripe using `StripeService.get_customer_by_id`.
    *   If the customer is found in Stripe, no further action is taken regarding customer creation.
    *   If the `stripe_customer_id` exists in the DB but the customer is *not* found in Stripe (e.g., deleted in Stripe, or an invalid ID), a warning is logged, and the process proceeds to re-create the Stripe customer.
3.  **Create or Retrieve Stripe Customer**:
    *   If no `stripe_customer_id` is found in the DB, or if the existing one is invalid/not found in Stripe, the `StripeService.get_or_create_stripe_customer` method is called.

### `StripeService.get_or_create_stripe_customer` ([`backend/open_webui/utils/integrations/stripe/service.py`](backend/open_webui/utils/integrations/stripe/service.py:124))

This method ensures that every OWUI user has a corresponding Stripe customer record:

1.  **Lookup by Email**: It first attempts to find a Stripe customer using the user's email address via `StripeService.get_customer_by_email`.
2.  **Create New Customer**:
    *   If no existing Stripe customer is found by email, a new Stripe customer is created using `stripe.Customer.create`. The `keycloakId` (OAuth `sub`) is stored in the Stripe customer's metadata for future reference.
    *   Immediately after creating a new Stripe customer, a trial subscription is created for this customer using `StripeService.create_trial_subscription`. The trial period is configured by `STRIPE_TRIAL_PERIOD_DAYS`.
3.  **Update OWUI User Record**: If a new Stripe customer is created (or an existing one is re-created due to a mismatch), the `user.stripe_customer_id` in the OWUI database is updated with the new Stripe customer ID.

## 2. Handling Trial Expiration and Account Pending State

When a user's trial subscription ends, an external service (which receives Stripe webhooks) is responsible for updating the user's role in Keycloak (or the configured OAuth provider) and subsequently in OWUI.

### UI Behavior (`src/lib/components/layout/Overlay/AccountPending.svelte`)

The `AccountPending.svelte` component is designed to handle the state where a user's account is pending activation, typically after a trial subscription has ended.

1.  **Token Refresh Polling**:
    *   When a user is redirected to `AccountPending.svelte` with `payment_success=true` in the URL (indicating a successful payment, but the role update might be pending), the component initiates a polling mechanism.
    *   The `checkAndRefreshToken` function is called repeatedly at intervals defined by `PAYMENT_POLLING_INTERVAL_MS` (see [`src/lib/components/layout/Overlay/AccountPending.svelte`](src/lib/components/layout/Overlay/AccountPending.svelte:21)).
    *   This function attempts to refresh the user's token using `userSignRefreshToken`.
    *   If a new token is successfully obtained (implying the user's role has been updated by the external webhook service), the polling stops, and the user is redirected to the home page (`/`).
    *   If the maximum number of polling attempts (`PAYMENT_MAX_POLLING_ATTEMPTS`) is reached without a successful token refresh, an error message is displayed to the user.
2.  **"Proceed to Payment" Button**:
    *   The component displays a "Proceed to Payment" button (see [`src/lib/components/layout/Overlay/AccountPending.svelte`](src/lib/components/layout/Overlay/AccountPending.svelte:137)).
    *   When clicked, this button triggers the `createCheckoutSession` function from `$lib/apis/payments`. This function, in turn, calls the backend endpoint `/users/stripe/checkout`.

### Backend Checkout Session Creation (`backend/open_webui/routers/users.py`)

The `/users/stripe/checkout` endpoint in [`backend/open_webui/routers/users.py`](backend/open_webui/routers/users.py:515) is responsible for creating a Stripe Checkout Session:

1.  **User Verification**: It retrieves the current user's details, including their `stripe_customer_id`.
2.  **Checkout Session Creation**: It calls `StripeService.create_checkout_session` with the user's Stripe customer ID, the `STRIPE_CHECKOUT_PRICE_ID`, and provided success/cancel URLs.
3.  **Redirection**: Upon successful creation, it returns the `checkout_url` from the Stripe session, to which the frontend redirects the user to complete the payment.

## 3. Stripe Webhook Processing (External Service)

While not directly part of the OWUI codebase provided, the workflow relies on an external service that handles Stripe webhooks. This service is crucial for:

1.  **Receiving Stripe Events**: Listening for events such as `customer.subscription.updated`, `customer.subscription.deleted`, or `checkout.session.completed`.
2.  **Updating User Roles**: Based on these events, the external service updates the user's role in Keycloak (or the OAuth provider). For example, if a subscription becomes active, the user's role might be changed from "pending" to "user". If a subscription is canceled or expires, the role might revert to "pending" or a restricted role.
3.  **OWUI Token Refresh**: The change in the user's role in Keycloak will eventually propagate to OWUI when the user's token is refreshed (either automatically by the UI's polling mechanism or upon re-login).

## Summary of Flow:

1.  **User Login**: User logs in via OAuth.
2.  **Stripe Customer Sync**: `oauth.py` calls `StripeService.sync_stripe_customer`.
    *   If `user.stripe_customer_id` exists and is valid in Stripe, no action.
    *   If `user.stripe_customer_id` is missing or invalid, `StripeService.get_or_create_stripe_customer` is called.
        *   This function tries to find a customer by email.
        *   If not found, a new Stripe customer is created, and a trial subscription is immediately added.
        *   The `user.stripe_customer_id` in OWUI's DB is updated.
3.  **Trial Expiration**: External webhook service detects trial end, updates user role in Keycloak/OAuth to a "pending" state.
4.  **UI Redirect**: OWUI UI detects the updated role (via token refresh) and redirects the user to `AccountPending.svelte`.
5.  **Payment Prompt**: `AccountPending.svelte` displays "Account Activation Pending" and a "Proceed to Payment" button.
6.  **Checkout Session**: User clicks "Proceed to Payment", which calls `/users/stripe/checkout`.
    *   This endpoint uses `StripeService.create_checkout_session` to generate a Stripe Checkout URL.
7.  **Stripe Payment**: User is redirected to Stripe to complete payment.
8.  **Payment Success & Webhook**: Upon successful payment, Stripe sends a webhook to the external service.
9.  **Role Update**: External service updates user's role in Keycloak/OAuth to an "active" state.
10. **UI Token Refresh**: `AccountPending.svelte` continues polling for token refresh. When the token reflects the active role, the user is redirected to the home page.