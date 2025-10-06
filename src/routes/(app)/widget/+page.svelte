<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { widgetMode, widgetConfig } from '$lib/stores';
	import Chat from '$lib/components/chat/Chat.svelte';
	import { getSessionUser } from '$lib/apis/auths';

	// Widget data passed from parent
	let widgetData = {
		fileId: '',
		fileName: '',
		title: 'Talk to Data',
		context: ''
	};

	// Extract widget parameters from URL
	$: {
		const urlParams = new URLSearchParams($page.url.search);
		widgetMode.set(true);

		widgetConfig.set({
			theme: urlParams.get('theme') || 'system',
			width: urlParams.get('width') || '100%',
			height: urlParams.get('height') || '100vh',
			model: urlParams.get('model') || '',
			position: urlParams.get('position') || 'fullscreen',
			zIndex: parseInt(urlParams.get('zIndex') || '9999')
		});


		widgetData.fileId = urlParams.get('fileId') || '';
		widgetData.fileName = urlParams.get('fileName') || '';
		widgetData.title = urlParams.get('title') || 'Talk to Data';
	}

	onMount(async () => {
		// Initialize authentication for widget
		try {
			// Try to get token from URL parameter or localStorage
			const urlParams = new URLSearchParams(window.location.search);
			const token = urlParams.get('token') || localStorage.getItem('token') || '';
			
			if (token) {
				await getSessionUser(token);
			}
		} catch (error) {
			console.error('Widget authentication failed:', error);
		}

		// Listen for data from parent window
		window.addEventListener('message', handleParentMessage);

		// Notify parent window that widget is ready
		if (window.parent !== window) {
			window.parent.postMessage(
				{
					type: 'open-webui-widget-ready',
					origin: 'open-webui-widget'
				},
				'*'
			);
		}
	});

	onDestroy(() => {
		window.removeEventListener('message', handleParentMessage);
	});

	function handleParentMessage(event: MessageEvent) {
		// Only accept messages from parent window
		if (event.source !== window.parent) return;

		const { type, data } = event.data;

		switch (type) {
			case 'widget-set-data':
				// Update widget data from parent
				widgetData = { ...widgetData, ...data };
				console.log('Widget received data:', widgetData);
				break;

			case 'widget-close':
				// Parent wants to close the widget
				sendMessageToParent('widget-closed');
				break;
		}
	}

	function sendMessageToParent(type: string, data?: any) {
		if (window.parent !== window) {
			window.parent.postMessage(
				{
					type,
					data,
					origin: 'open-webui-widget'
				},
				'*'
			);
		}
	}

	function closeWidget() {
		sendMessageToParent('widget-close-request');
	}
</script>

<svelte:head>
	<title>{widgetData.title}</title>
	<style>
		:global(body) {
			margin: 0;
			padding: 0;
			overflow: hidden;
		}
	</style>
</svelte:head>

<div class="widget-modal" class:fullscreen={$widgetConfig.position === 'fullscreen'}>
	<!-- Modal Header -->
	<div class="widget-header">
		<div class="header-content">
			<div class="header-icon">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="24"
					height="24"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
					<line x1="9" y1="10" x2="15" y2="10"></line>
					<line x1="12" y1="7" x2="12" y2="13"></line>
				</svg>
			</div>
			<div class="header-text">
				<h2>{widgetData.title}</h2>
				<!-- {#if widgetData.fileName}
					<p class="file-name">{widgetData.fileName}</p>
				{/if} -->
			</div>
		</div>
		<button class="close-button" on:click={closeWidget} aria-label="Close widget">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="24"
				height="24"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<line x1="18" y1="6" x2="6" y2="18"></line>
				<line x1="6" y1="6" x2="18" y2="18"></line>
			</svg>
		</button>
	</div>

	<!-- Chat Content -->
	<div class="widget-content">
		<Chat chatIdProp={widgetData.fileId} />
	</div>

	<!-- Debug Info (remove in production)
	{#if widgetData.fileId}
		<div class="debug-info">
			<small>File ID: {widgetData.fileId}</small>
		</div>
	{/if} -->
</div>

<style>
	.widget-modal {
		width: 100%;
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: var(--color-bg, #ffffff);
	}

	.widget-modal.fullscreen {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 9999;
	}

	.widget-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 16px 20px;
		border-bottom: 1px solid var(--color-border, #e5e7eb);
		background: var(--color-header-bg, #f9fafb);
		flex-shrink: 0;
	}

	.header-content {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.header-icon {
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border-radius: 8px;
	}

	.header-text h2 {
		margin: 0;
		font-size: 18px;
		font-weight: 600;
		color: var(--color-text, #111827);
	}

	.file-name {
		margin: 4px 0 0 0;
		font-size: 12px;
		color: var(--color-text-secondary, #6b7280);
	}

	.close-button {
		width: 36px;
		height: 36px;
		display: flex;
		align-items: center;
		justify-content: center;
		border: none;
		background: transparent;
		color: var(--color-text-secondary, #6b7280);
		cursor: pointer;
		border-radius: 6px;
		transition: all 0.2s;
	}

	.close-button:hover {
		background: var(--color-hover-bg, #f3f4f6);
		color: var(--color-text, #111827);
	}

	.widget-content {
		flex: 1;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	.debug-info {
		position: absolute;
		bottom: 10px;
		left: 10px;
		padding: 4px 8px;
		background: rgba(0, 0, 0, 0.7);
		color: white;
		border-radius: 4px;
		font-size: 11px;
		z-index: 10000;
	}

	/* Dark mode support */
	@media (prefers-color-scheme: dark) {
		.widget-modal {
			--color-bg: #1f2937;
			--color-header-bg: #111827;
			--color-border: #374151;
			--color-text: #f9fafb;
			--color-text-secondary: #9ca3af;
			--color-hover-bg: #374151;
		}
	}
</style>
