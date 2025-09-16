<script lang="ts">
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import ArrowTurnDownRight from '$lib/components/icons/ArrowTurnDownRight.svelte';
	import { onMount, tick, getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	const i18n: Writable<i18nType> = getContext('i18n');

	export let followUps: (string | { title: string[]; content: string })[] = [];
	export let onClick: (followUp: string) => void = () => {};
	export let onSelect: (e: { type: string; data: string }) => void = () => {};
	export let title: string | null = null;
	export let isSuggestion: boolean = false;
</script>

<div class="mt-4">
	<div class="text-sm font-medium">
		{title ?? $i18n.t('Follow up')}
	</div>

	<div class="flex flex-col text-left gap-1 mt-1.5">
		{#each followUps as followUp, idx (idx)}
			{@const isSuggestionFormat = typeof followUp === 'object' && followUp !== null && 'title' in followUp && 'content' in followUp}
			{@const displayText = isSuggestionFormat ? followUp.title[0] : followUp}
			{@const tooltipText = isSuggestionFormat ? followUp.content : followUp}
			{@const clickData = isSuggestionFormat ? followUp.content : followUp}
			
			<!-- svelte-ignore a11y-no-static-element-interactions -->
			<!-- svelte-ignore a11y-click-events-have-key-events -->
			<Tooltip content={tooltipText} placement="top-start" className="line-clamp-1">
				<div
					class=" mr-2 py-1.5 bg-transparent text-left text-sm flex items-center gap-2 px-1.5 text-gray-500 dark:text-gray-400 hover:text-black dark:hover:text-white transition cursor-pointer"
					on:click={() => {
						if (isSuggestion) {
							onSelect({ type: 'prompt', data: clickData });
						} else {
							onClick(clickData);
						}
					}}
					title={tooltipText}
					aria-label={tooltipText}
				>
					<ArrowTurnDownRight className="size-3.5" />

					<div class="line-clamp-1">
						{displayText}
					</div>
				</div>
			</Tooltip>

			{#if idx < followUps.length - 1}
				<hr class="border-gray-100 dark:border-gray-850" />
			{/if}
		{/each}
	</div>
</div>
