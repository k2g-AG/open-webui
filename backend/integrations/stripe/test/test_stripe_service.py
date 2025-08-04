import uuid
from backend.integrations.stripe.service import StripeService

def test_get_customer_by_email():
    email = "nonexistent_" + str(uuid.uuid4())[:8] + "@example.com"
    customer = StripeService.get_customer_by_email(email)
    assert customer is None
    print("✔ get_customer_by_email — OK (not found case)")

def test_create_customer_and_trial_subscription():
    email = "test_" + str(uuid.uuid4())[:8] + "@example.com"
    name = "Test User"
    metadata = {"keycloakId": str(uuid.uuid4())}

    customer = StripeService.create_customer(email, name, metadata)
    assert customer is not None and customer["email"] == email
    print("✔ create_customer — OK")

    customer_id = customer["id"]
    subscription = StripeService.create_trial_subscription(customer_id)
    assert subscription is not None and subscription["customer"] == customer_id
    print("✔ create_trial_subscription — OK")
