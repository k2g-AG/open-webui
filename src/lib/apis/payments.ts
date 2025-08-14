import { WEBUI_API_BASE_URL } from '../constants';

export const createCheckoutSession = async (token: string) => {
    try {
        const successUrl = 'https://oi.k2g.ai';
        const cancelUrl = 'https://oi.k2g.ai';

        const response = await fetch(`${WEBUI_API_BASE_URL}/payments/create-checkout-session`, {
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
            throw new Error(errorData.detail || 'Failed to create checkout session');
        }

        return await response.json();
    } catch (error) {
        console.error('Error creating checkout session:', error);
        return null;
    }
};