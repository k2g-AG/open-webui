<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onDestroy, onMount, getContext, createEventDispatcher } from 'svelte';
	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	import { artifactCode, chatId, settings, showArtifacts, showControls } from '$lib/stores';
	import { copyToClipboard, createMessagesList } from '$lib/utils';

	import ArrowsPointingOut from '../icons/ArrowsPointingOut.svelte';
	import Tooltip from '../common/Tooltip.svelte';
	import SvgPanZoom from '../common/SVGPanZoom.svelte';
	import ArrowDownTray from '../icons/ArrowDownTray.svelte';

	export let inContent;
	export let inLang;
	export let inCollapsed = true; // set to false if you want to expand after timeout
	export let overlay = false;
	export let expandTimeout = 5; // seconds timeout to auto expand from last data update

	let contents: Array<{ type: string; content: string }> = [];
	let iframeElement: HTMLIFrameElement;

	let selectedContentIdx = 0;

	let copied = false;
	let collapsed = true;

	let timeoutId;

	function startTimer() {
		timeoutId = setTimeout(() => {
			collapsed = inCollapsed;
		}, expandTimeout * 1000); // 5 seconds default
	}

	onDestroy(() => {
		clearTimeout(timeoutId); // Clear the timeout when the component is destroyed
	});


	$: if (inContent && inLang) {
		clearTimeout(timeoutId);
		getContents();
		if (!inCollapsed) {
			startTimer();
		}
	}

	const getContents = () => {
		contents = [];
		if (inContent) {
			let lang = inLang ?? '';
			let code = inContent ?? '';

			const codeBlockContents = inContent.match(/```[\s\S]*?```/g);
			let codeBlocks = [];

			if (codeBlockContents) {
				codeBlockContents.forEach((block) => {
					lang = block.split('\n')[0].replace('```', '').trim().toLowerCase();
					code = block.replace(/```[\s\S]*?\n/, '').replace(/```$/, '');
					codeBlocks.push({ lang, code });
				});
			} else {
				codeBlocks.push({ lang, code });
			}

			let htmlContent = '';
			let cssContent = '';
			let jsContent = '';

			codeBlocks.forEach((block) => {
				const { lang, code } = block;

				if (lang === 'html') {
					htmlContent += code + '\n';
				} else if (lang === 'css') {
					cssContent += code + '\n';
				} else if (lang === 'javascript' || lang === 'js') {
					jsContent += code + '\n';
				}
			});

			const inlineHtml = inContent.match(/<html>[\s\S]*?<\/html>/gi);
			const inlineCss = inContent.match(/<style>[\s\S]*?<\/style>/gi);
			const inlineJs = inContent.match(/<script>[\s\S]*?<\/script>/gi);

			if (inlineHtml) {
				inlineHtml.forEach((block) => {
					const content = block.replace(/<\/?html>/gi, ''); // Remove <html> tags
					htmlContent += content + '\n';
				});
			}
			if (inlineCss) {
				inlineCss.forEach((block) => {
					const content = block.replace(/<\/?style>/gi, ''); // Remove <style> tags
					cssContent += content + '\n';
				});
			}
			if (inlineJs) {
				inlineJs.forEach((block) => {
					const content = block.replace(/<\/?script>/gi, ''); // Remove <script> tags
					jsContent += content + '\n';
				});
			}

			if (htmlContent || cssContent || jsContent) {
				const renderedContent = `
					<!DOCTYPE html>
					<html lang="en">
					<head>
						<meta charset="UTF-8">
						<meta name="viewport" content="width=device-width, initial-scale=1.0">
						<${''}style>
							body {
								background-color: white; /* Ensure the iframe has a white background */
							}

							${cssContent}
						</${''}style>
					</head>
					<body>
						${htmlContent}

						<${''}script>
							${jsContent}
						</${''}script>
					</body>
					</html>
				`;
				contents = [...contents, { type: 'iframe', content: renderedContent }];
			} else {
				// Check for SVG content
				for (const block of codeBlocks) {
					if (block.lang === 'svg' || (block.lang === 'xml' && block.code.includes('<svg'))) {
						contents = [...contents, { type: 'svg', content: block.code }];
					}
				}
			}
		}

		selectedContentIdx = contents ? contents.length - 1 : 0;
	};

	const collapseIFrameBlock = () => {
		collapsed = !collapsed;
	};

	const showFullScreen = () => {
		if (iframeElement.requestFullscreen) {
			iframeElement.requestFullscreen();
		} else if (iframeElement.webkitRequestFullscreen) {
			iframeElement.webkitRequestFullscreen();
		} else if (iframeElement.msRequestFullscreen) {
			iframeElement.msRequestFullscreen();
		}
	};

	const downloadArtifact = () => {
		const blob = new Blob([contents[selectedContentIdx].content], { type: 'text/html' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `artifact-${$chatId}-${selectedContentIdx}.html`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	};

	onMount(() => {
		getContents();
		artifactCode.subscribe((value) => {
			if (contents.length > 0) {
				const codeIdx = contents.findIndex((content) => content.content.includes(value));
				selectedContentIdx = codeIdx !== -1 ? codeIdx : 0;
			}
		});
	});
</script>

{#if contents.length > 0}
	<div class=" w-full h-full relative flex flex-col bg-gray-50 dark:bg-gray-850">
		<div class="w-full h-full flex flex-col flex-1 relative">
			<div class="pointer-events-auto z-20 flex justify-between items-center p-2.5 font-primar text-gray-900 dark:text-white">
				<div class="flex-1 flex items-center justify-between pr-1">
					<div class="flex items-center space-x-2">
						<div class="flex items-center gap-0.5 self-center min-w-fit" dir="ltr">
						</div>
					</div>

					<div class="flex items-center gap-1.5">
						<button
							class="bg-none border-none text-xs bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-md p-0.5"
							on:click={collapseIFrameBlock}
						>
							<div>
								{collapsed ? $i18n.t('Expand') : $i18n.t('Collapse')}
							</div>
						</button>
						<button
							class="copy-code-button bg-none border-none text-xs bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-md px-1.5 py-0.5"
							on:click={() => {
								copyToClipboard(contents[selectedContentIdx].content);
								copied = true;

								setTimeout(() => {
									copied = false;
								}, 2000);
							}}>{copied ? $i18n.t('Copied') : $i18n.t('Copy')}</button
						>

						<Tooltip content={$i18n.t('Download')}>
							<button
								class=" bg-none border-none text-xs bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-md p-0.5"
								on:click={downloadArtifact}
							>
								<ArrowDownTray className="size-3.5" />
							</button>
						</Tooltip>

						{#if contents[selectedContentIdx].type === 'iframe'}
							<Tooltip content={$i18n.t('Open in full screen')}>
								<button
									class=" bg-none border-none text-xs bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-md p-0.5"
									on:click={showFullScreen}
								>
									<ArrowsPointingOut className="size-3.5" />
								</button>
							</Tooltip>
						{/if}
					</div>
				</div>
			</div>

			{#if overlay}
				<div class=" absolute top-0 left-0 right-0 bottom-0 z-10"></div>
			{/if}

			{#if !collapsed}
				<div class="flex-1 w-full h-full">
					<div class=" h-full flex flex-col">
						<div class="max-w-full w-full h-full">
							{#if contents[selectedContentIdx].type === 'iframe'}
								<iframe
									bind:this={iframeElement}
									title="Content"
									srcdoc={contents[selectedContentIdx].content}
									class="w-full border-0 h-full rounded-none"
									onload="this.style.height=(this.contentWindow.document.body.scrollHeight+20)+'px';"
								></iframe>
							{:else if contents[selectedContentIdx].type === 'svg'}
								<SvgPanZoom
									className=" w-full h-full max-h-full overflow-hidden"
									svg={contents[selectedContentIdx].content}
								/>
							{/if}
						</div>
					</div>
				</div>
			{/if}

		</div>
	</div>
{/if}
