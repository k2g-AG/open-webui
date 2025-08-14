<script lang="ts">
	import { createStripeCheckoutSession } from '$lib/apis/users';
	import { user } from '$lib/stores';
	import { get } from 'svelte/store';

	export let buttonText = 'Subscribe Now';
	export let successUrl = `${window.location.origin}/payment/success?session_id={CHECKOUT_SESSION_ID}`;
	export let cancelUrl = `${window.location.origin}/payment/cancel`;

	let loading = false;

	async function startCheckout() {
		loading = true;
		try {
			const currentUser = get(user);
			if (!currentUser?.token) {
				throw new Error('User not authenticated');
			}

			const result = await createStripeCheckoutSession(
				currentUser.token,
				successUrl,
				cancelUrl
			);

			if (result?.checkout_url) {
				// Redirect to Stripe checkout
				window.location.href = result.checkout_url;
			} else {
				throw new Error('Failed to create checkout session');
			}
		} catch (error) {
			console.error('Stripe checkout error:', error);
			alert('Error creating payment session. Please try again.');
		} finally {
			loading = false;
		}
	}
</script>

<button
	on:click={startCheckout}
	disabled={loading}
	class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
>
	{#if loading}
		<svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
			<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
			<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
		</svg>
		Loading...
	{:else}
		{buttonText}
	{/if}
</button>