<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { widgetMode, widgetConfig } from '$lib/stores';
	import Chat from '$lib/components/chat/Chat.svelte';
	import { getSessionUser } from '$lib/apis/auths';

	// Extract widget parameters from URL
	$: {
		const urlParams = new URLSearchParams($page.url.search);
		widgetMode.set(true);
		
		widgetConfig.set({
			theme: urlParams.get('theme') || 'system',
			width: urlParams.get('width') || '360px',
			height: urlParams.get('height') || '560px',
			model: urlParams.get('model') || '',
			position: urlParams.get('position') || 'bottom-right',
			zIndex: parseInt(urlParams.get('zIndex') || '9999')
		});
	}

	onMount(async () => {
		// Initialize authentication for widget
		try {
			await getSessionUser();
		} catch (error) {
			console.error('Widget authentication failed:', error);
		}

		// Notify parent window that widget is ready
		if (window.parent !== window) {
			window.parent.postMessage({
				type: 'open-webui-widget-ready',
				origin: 'open-webui-widget'
			}, '*');
		}
	});
</script>

<svelte:head>
	<title>Open WebUI Widget</title>
	<style>
		:global(body) {
			margin: 0;
			padding: 0;
			overflow: hidden;
		}
	</style>
</svelte:head>

<div class="widget-container" style="width: {$widgetConfig.width}; height: {$widgetConfig.height};">
	<Chat />
</div>

<style>
	.widget-container {
		border-radius: 12px;
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
		overflow: hidden;
	}
</style>
