<script lang="ts">
	import { getAdminDetails, userSignRefreshToken } from '$lib/apis/auths';
	import { createCheckoutSession } from '$lib/apis/payments';
	import { onMount, tick, getContext, onDestroy } from 'svelte';
	import { config } from '$lib/stores';
	import { WEBUI_BASE_URL, PAYMENT_POLLING_INTERVAL_MS, PAYMENT_MAX_POLLING_ATTEMPTS } from '$lib/constants';

	const i18n = getContext('i18n');

	let adminDetails = null;
   // Reactive variable to control the visibility of the error message
   let showPollingErrorMessage = false;
   // Reactive variable to control the visibility of the loader animation
   let showPollingLoader = false;

	onMount(async () => {
		adminDetails = await getAdminDetails(localStorage.token).catch((err) => {
			console.error(err);
			return null;
		});

   let pollingInterval: NodeJS.Timeout;
   let pollingAttempts = 0;

   /**
    * Function to check and refresh the user's token.
    * This is called repeatedly during the polling process.
    */
   const checkAndRefreshToken = async () => {
       pollingAttempts++;
       console.log(`Attempting to refresh token (attempt ${pollingAttempts}/${PAYMENT_MAX_POLLING_ATTEMPTS})...`);
       try {
           const newToken = await userSignRefreshToken(localStorage.token);
           if (newToken && newToken.access_token) {
               // If a new token is successfully obtained, it implies the user's role might have been updated.
               // In a more robust system, you might fetch user details to explicitly confirm the role.
               localStorage.setItem('token', newToken.access_token);
               console.log('Token refreshed successfully after payment. Redirecting...');
               clearInterval(pollingInterval); // Stop polling as the token is updated
               showPollingLoader = false; // Hide loader
               window.location.href = '/'; // Redirect to home page
           } else {
               console.log('Token refresh failed, retrying...');
           }
       } catch (error) {
           console.error('Error refreshing token:', error);
       }

       // If max polling attempts are reached, stop polling and show an error message
       if (pollingAttempts >= PAYMENT_MAX_POLLING_ATTEMPTS) {
           console.warn('Max polling attempts reached. Stopping polling.');
           clearInterval(pollingInterval);
           showPollingErrorMessage = true; // Show error message to the user
           showPollingLoader = false; // Hide loader
       }
   };

   // Check if the URL contains the 'payment_success=true' parameter
   const urlParams = new URLSearchParams(window.location.search);
   if (urlParams.get('payment_success') === 'true') {
       console.log('Payment success detected. Starting token refresh polling...');
       showPollingLoader = true; // Show loader when polling starts
       checkAndRefreshToken(); // Perform an initial check immediately
       // Start polling at defined intervals
       pollingInterval = setInterval(checkAndRefreshToken, PAYMENT_POLLING_INTERVAL_MS);
   }

   // Cleanup function to clear the polling interval when the component is destroyed
   onDestroy(() => {
       if (pollingInterval) {
           clearInterval(pollingInterval);
       }
   });
</script>
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
						{$i18n.t('Account Activation Pending')}<br />
						{$i18n.t('Contact Admin for WebUI Access')}
					{/if}
				</div>

				<div
					class=" mt-4 text-center text-sm dark:text-gray-200 w-full"
					style="white-space: pre-wrap;"
				>
					{#if ($config?.ui?.pending_user_overlay_content ?? '').trim() !== ''}
						{$config.ui.pending_user_overlay_content}
					{:else}
						{$i18n.t('Your account status is currently pending activation.')}{'\n'}{$i18n.t(
							'To access the WebUI, please reach out to the administrator. Admins can manage user statuses from the Admin Panel.'
						)}
					{/if}
				</div>

				{#if adminDetails}
					<div class="mt-4 text-sm font-medium text-center">
						<div>{$i18n.t('Admin')}: {adminDetails.name} ({adminDetails.email})</div>
					</div>
				{/if}

               {#if showPollingErrorMessage}
                   <!-- Display error message if polling fails -->
                   <div class="mt-4 text-center text-red-500 text-sm">
                       {$i18n.t('Failed to update account status. Please try again later or contact support.')}
                   </div>
               {/if}

				<div class=" mt-6 mx-auto relative group w-fit">
                   {#if showPollingLoader}
                       <!-- Display loader animation while polling is active -->
                       <div class="flex justify-center items-center">
                           <svg class="animate-spin h-5 w-5 mr-3 text-gray-600 dark:text-gray-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                               <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                               <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                           </svg>
                           <span class="dark:text-gray-200">{$i18n.t('Updating account status...')}</span>
                       </div>
                   {:else}
                       <!-- Display "Proceed to Payment" button if not polling -->
                       <button
                           type="button"
                           class="relative z-20 flex px-5 py-2 rounded-full bg-white border border-gray-100 dark:border-none hover:bg-gray-100 text-gray-700 transition font-medium text-sm"
                           on:click={async () => {
                               const checkoutSession = await createCheckoutSession(localStorage.token);
                               if (checkoutSession && checkoutSession.checkout_url) {
                                   window.location.href = checkoutSession.checkout_url;
                               } else {
                                   // Fallback to check again if checkout session creation fails
                                   // location.href = '/';
                                   console.error('Failed to create checkout session:', checkoutSession);
                               }
                           }}
                       >
                           {$i18n.t('Proceed to Payment')}
                       </button>
                   {/if}

					<button
						class="text-xs text-center w-full mt-2 text-gray-400 underline"
						on:click={async () => {
							localStorage.removeItem('token');
							location.href = `${WEBUI_BASE_URL}/oauth/oidc/login`;
						}}>{$i18n.t('Sign Out')}</button
					>
				</div>
			</div>
		</div>
	</div>
</div>
