<script lang="ts">
	import { getAdminDetails, userSignRefreshToken } from '$lib/apis/auths';
	import { createCheckoutSession } from '$lib/apis/payments';
	import { onMount, onDestroy } from 'svelte';
	import { config } from '$lib/stores';
	import {
		WEBUI_BASE_URL,
		PAYMENT_POLLING_INTERVAL_MS,
		PAYMENT_MAX_POLLING_ATTEMPTS
	} from '$lib/constants';
	import { goto } from '$app/navigation';

	let adminDetails: any = null;
	// Reactive variable to control the visibility of the error message
	let showPollingErrorMessage: boolean = false;
	// Reactive variable to control the visibility of the loader animation
	let showPollingLoader: boolean = false;

	let pollingInterval: number | undefined;
	let pollingAttempts: number = 0;

	/**
	 * Function to check and refresh the user's token.
	 * This is called repeatedly during the polling process.
	 */
	const checkAndRefreshToken = async () => {
		pollingAttempts++;
		console.log(
			`Attempting to refresh token (attempt ${pollingAttempts}/${PAYMENT_MAX_POLLING_ATTEMPTS})...`
		);

		// Check if token exists in localStorage
		const currentToken = localStorage.getItem('token');
		if (!currentToken) {
			console.error('No token found in localStorage');
			if (pollingInterval !== undefined) {
				clearInterval(pollingInterval);
			}
			showPollingErrorMessage = true;
			return;
		}

		try {
			const newToken = await userSignRefreshToken(currentToken);
			if (newToken && newToken.access_token) {
				// If a new token is successfully obtained, it implies the user's role might have been updated.
				// In a more robust system, you might fetch user details to explicitly confirm the role.
				localStorage.setItem('token', newToken.access_token);
				console.log('Token refreshed successfully after payment. Redirecting...');
				if (pollingInterval !== undefined) {
					clearInterval(pollingInterval); // Stop polling as the token is updated
				}
				await goto('/', { replaceState: true }); // Redirect to home page and clear URL parameter
			} else {
				console.log('Token refresh failed, retrying...');
			}
		} catch (error) {
			console.error('Error refreshing token:', error);
		}

		// If max polling attempts are reached, stop polling and show an error message
		if (pollingAttempts >= PAYMENT_MAX_POLLING_ATTEMPTS) {
			console.warn('Max polling attempts reached. Stopping polling.');
			if (pollingInterval !== undefined) {
				clearInterval(pollingInterval);
			}
			showPollingErrorMessage = true; // Show error message to the user
		}
	};

	onMount(async () => {
		// Get admin details if token exists
		const token = localStorage.getItem('token');
		if (token) {
			adminDetails = await getAdminDetails(token).catch((err: any) => {
				console.error('Failed to get admin details:', err);
				return null;
			});
		}

		// Check if the URL contains the 'payment_success=true' parameter
		const urlParams = new URLSearchParams(window.location.search);
		if (urlParams.get('payment_success') === 'true') {
			console.log('Payment success detected. Starting token refresh polling...');
			checkAndRefreshToken(); // Perform an initial check immediately
			// Start polling at defined intervals
			pollingInterval = setInterval(checkAndRefreshToken, PAYMENT_POLLING_INTERVAL_MS);
		}
	});

	// Cleanup function to clear the polling interval when the component is destroyed
	onDestroy(() => {
		if (pollingInterval !== undefined) {
			clearInterval(pollingInterval);
		}
	});
</script>

<div class="fixed w-full h-full flex z-999">
	<div
		class="absolute w-full h-full backdrop-blur-lg bg-white/10 dark:bg-gray-900/50 flex justify-center"
	>
		<div class="m-auto pb-10 flex flex-col justify-center">
			<div class="max-w-md">
				<div
					class="text-center dark:text-white text-2xl font-medium z-50"
					style="white-space: pre-wrap;"
				>
					{#if ($config?.ui?.pending_user_overlay_title ?? '').trim() !== ''}
						{$config.ui.pending_user_overlay_title}
					{:else}
						<div>Your subscription has ended</div>
					{/if}
				</div>

				<div
					class=" mt-4 text-center text-sm dark:text-gray-200 w-full"
					style="white-space: pre-wrap;"
				>
					{#if ($config?.ui?.pending_user_overlay_content ?? '').trim() !== ''}
						{$config.ui.pending_user_overlay_content}
					{:else}
						<div class="mt-2">Please renew your subscription to continue using the service.</div>
					{/if}
				</div>

				{#if adminDetails}
					<div class="mt-4 text-sm font-medium text-center">
						<div>Admin: {adminDetails.name} ({adminDetails.email})</div>
					</div>
				{/if}

				{#if showPollingErrorMessage}
					<!-- Display error message if polling fails -->
					<div class="mt-4 text-center text-red-500 text-sm">
						Failed to update account status. Please try again later or contact support.
					</div>
				{/if}

				<div class=" mt-6 mx-auto relative group w-fit">
					<!-- Display "Proceed to Payment" button -->
					<button
						type="button"
						class="relative z-20 flex px-5 py-2 rounded-full bg-white border border-gray-100 dark:border-none hover:bg-gray-100 text-gray-700 transition font-medium text-sm"
						on:click={async () => {
							try {
								const token = localStorage.getItem('token');
								if (!token) {
									console.error('No token found in localStorage');
									return;
								}

								const checkoutSession = await createCheckoutSession(token);

								if (!checkoutSession) {
									throw new Error('Failed to create checkout session - response was empty');
								}

								if (!checkoutSession.checkout_url) {
									throw new Error('Checkout URL is missing from response');
								}

								// Redirect to checkout
								window.location.assign(checkoutSession.checkout_url);
							} catch (error) {
								console.error('Error creating checkout session:', error);
								showPollingErrorMessage = true;
							}
						}}
					>
						Proceed to Payment
					</button>

					<button
						class="text-xs text-center w-full mt-2 text-gray-400 underline"
						on:click={() => {
							localStorage.removeItem('token');
							window.location.assign(`${WEBUI_BASE_URL}/oauth/oidc/login`);
						}}
					>
						Sign Out
					</button>
				</div>
			</div>
		</div>
	</div>
</div>
