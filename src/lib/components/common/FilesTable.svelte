<script lang="ts">
	export let handleClose: () => void; // Accept close function
	export let setFile: (file: any) => void;
	export let allFiles = [];
	export let headerTitle = '';

	function formatSize(bytes: number) {
		return (bytes / 1_000_000).toFixed(1);
	}
	function formatDate(dateStr: string) {
		const d = new Date(dateStr * 1000);
		const day = String(d.getDate()).padStart(2, '0');
		const month = String(d.getMonth() + 1).padStart(2, '0');
		const year = d.getFullYear();
		const time = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
		return `${day}.${month}.${year} at ${time}`;
	}
</script>

<div class="modal">
	<h2 class="title">{headerTitle || 'Uploaded datasets'}</h2>
	<div class="table-wrapper">
		<table class="file-table">
			<thead>
				<tr>
					<th class="pl-4 md:pl-6">File name</th>
					<th class="format-col">Format</th>
					<th class="hidden md:table-cell">Headers</th>
					<th class="hidden md:table-cell">Lines</th>
					<th class="hidden sm:table-cell">Size, Mb</th>
					<th class="hidden lg:table-cell">Date uploaded</th>
					<th></th>
				</tr>
			</thead>
			<tbody>
				{#each allFiles as file}
					<tr>
						<td class="pl-4 md:pl-6 max-w-[200px] sm:max-w-xs md:max-w-md truncate">
							<div class="truncate">{file.filename}</div>
						</td>
						<td class="format-col">
							<span class="tag {file.filename?.split('.')?.pop()?.toUpperCase()}"
								>{file.filename?.split('.')?.pop()?.toUpperCase()}</span
							>
						</td>
						<td class="hidden md:table-cell">{''}</td>
						<td class="hidden md:table-cell">{''}</td>
						<td class="hidden sm:table-cell">{formatSize(file.meta.size)}</td>
						<td class="hidden lg:table-cell">{formatDate(file.created_at)}</td>
						<td>
							<button
								class="upload-btn"
								on:click={() => {
									setFile(file);
								}}>Upload</button
							>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
	<div class="footer">
		<button class="cancel-btn" on:click={handleClose}>Cancel</button>
	</div>
</div>

<style>
	.modal {
		background: rgb(255 255 255);
		border-radius: 12px;
		width: 100%;
		margin: auto;
		font-family: system-ui, sans-serif;
	}

	:global(.dark) .modal {
		background: rgb(31 41 55);
	}

	.title {
		padding: 1rem 1rem 0.75rem 1rem;
		font-size: 17px;
		font-weight: 600;
		margin-bottom: 1rem;
		border-bottom: 1px solid rgb(229 231 235);
		color: rgb(17 24 39);
	}

	:global(.dark) .title {
		border-bottom-color: rgb(55 65 81);
		color: rgb(243 244 246);
	}

	@media (min-width: 768px) {
		.title {
			padding: 1.5rem 1.5rem 1rem 1.5rem;
		}
	}

	.table-wrapper {
		overflow-x: auto;
		padding: 0.5rem 0.5rem 1rem 0.5rem;
	}

	@media (min-width: 768px) {
		.table-wrapper {
			padding: 1rem 1.5rem 1.5rem 1.5rem;
		}
	}

	.file-table {
		width: 100%;
		border-collapse: collapse;
		min-width: 500px;
	}

	.file-table th,
	.file-table td {
		padding: 0.75rem 0.75rem;
		text-align: left;
		border-bottom: 1px solid rgb(229 231 235);
		font-size: 13px;
		color: rgb(31 41 55);
		vertical-align: middle;
	}

	:global(.dark) .file-table th,
	:global(.dark) .file-table td {
		border-bottom-color: rgb(55 65 81);
		color: rgb(209 213 219);
	}

	@media (min-width: 768px) {
		.file-table th,
		.file-table td {
			padding: 1rem 1.25rem;
			font-size: 14px;
		}
	}

	.file-table tr:hover {
		background-color: rgb(249 250 251);
	}

	:global(.dark) .file-table tr:hover {
		background-color: rgb(55 65 81 / 0.3);
	}

	.file-table tr:hover .upload-btn {
		opacity: 1;
	}

	.file-table th {
		color: rgb(107 114 128);
		font-weight: 600;
		font-size: 11px;
		text-transform: uppercase;
		letter-spacing: 0.025em;
	}

	:global(.dark) .file-table th {
		color: rgb(156 163 175);
	}

	@media (min-width: 768px) {
		.file-table th {
			font-size: 12px;
		}
	}

	.format-col {
		width: 80px;
	}

	@media (min-width: 768px) {
		.format-col {
			width: 100px;
		}
	}

	.tag {
		display: inline-block;
		padding: 3px 8px;
		border-radius: 6px;
		font-size: 11px;
		font-weight: 600;
		text-transform: uppercase;
		color: rgb(75 85 99);
		border: 1px solid rgb(156 163 175);
		background-color: rgb(243 244 246);
		white-space: nowrap;
	}

	:global(.dark) .tag {
		color: rgb(156 163 175);
		border-color: rgb(75 85 99);
		background-color: rgb(55 65 81);
	}

	@media (min-width: 768px) {
		.tag {
			padding: 4px 10px;
			font-size: 12px;
		}
	}

	.tag.XLSX {
		background-color: rgba(2, 214, 99, 0.1);
		color: rgba(2, 214, 99, 1);
		border: 1px solid rgba(2, 214, 99, 0.2);
	}

	:global(.dark) .tag.XLSX {
		background-color: rgba(2, 214, 99, 0.15);
		color: rgba(34, 197, 94, 1);
		border-color: rgba(2, 214, 99, 0.3);
	}

	.tag.CSV {
		background-color: rgba(155, 81, 224, 0.1);
		color: rgba(155, 81, 224, 1);
		border: 1px solid rgba(155, 81, 224, 0.2);
	}

	:global(.dark) .tag.CSV {
		background-color: rgba(155, 81, 224, 0.15);
		color: rgba(168, 85, 247, 1);
		border-color: rgba(155, 81, 224, 0.3);
	}

	.upload-btn {
		background-color: rgb(59 130 246);
		color: white;
		opacity: 0;
		padding: 0.375rem 0.75rem;
		border: none;
		border-radius: 4px;
		font-size: 13px;
		cursor: pointer;
		transition: opacity 0.2s, background-color 0.2s;
		white-space: nowrap;
	}

	:global(.dark) .upload-btn {
		background-color: rgb(59 130 246);
	}

	@media (min-width: 768px) {
		.upload-btn {
			font-size: 14px;
			padding: 0.375rem 0.875rem;
		}
	}

	.upload-btn:hover {
		opacity: 1;
		background-color: rgb(37 99 235);
	}

	:global(.dark) .upload-btn:hover {
		background-color: rgb(37 99 235);
	}

	@media (hover: none) {
		.upload-btn {
			opacity: 1;
		}
	}

	.footer {
		padding: 0.75rem 1rem;
		text-align: right;
		border-top: 1px solid rgb(229 231 235);
	}

	:global(.dark) .footer {
		border-top-color: rgb(55 65 81);
	}

	@media (min-width: 768px) {
		.footer {
			padding: 1rem 1.5rem;
		}
	}

	.cancel-btn {
		background: rgb(255 255 255);
		border: 1px solid rgb(209 213 219);
		color: rgb(55 65 81);
		padding: 0.375rem 0.875rem;
		border-radius: 6px;
		cursor: pointer;
		transition: background-color 0.2s;
		font-size: 14px;
	}

	:global(.dark) .cancel-btn {
		background: rgb(55 65 81);
		border-color: rgb(75 85 99);
		color: rgb(229 231 235);
	}

	.cancel-btn:hover {
		background-color: rgb(249 250 251);
	}

	:global(.dark) .cancel-btn:hover {
		background-color: rgb(75 85 99);
	}
</style>

