import { WEBUI_API_BASE_URL } from '../constants';

export const createCheckoutSession = async (token: string) => {
    console.log('Attempting to create Stripe checkout session...');
    try {
        const successUrl = 'https://oi.k2g.ai';
        const cancelUrl = 'https://oi.k2g.ai';

        console.log(`Sending request to ${WEBUI_API_BASE_URL}/stripe/checkout with successUrl: ${successUrl}, cancelUrl: ${cancelUrl}`);

        const response = await fetch(`${WEBUI_API_BASE_URL}/users/stripe/checkout`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({
                success_url: successUrl,
                cancel_url: cancelUrl
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('Failed to create checkout session. Server response:', errorData);
            throw new Error(errorData.detail || 'Failed to create checkout session');
        }

        const data = await response.json();
        console.log('Checkout session created successfully. Response data:', data);
        return data;
    } catch (error) {
        console.error('Error creating checkout session:', error);
        return null;
    }
};