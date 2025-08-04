<script lang="ts">
	export let handleClose: () => void; // Accept close function
	export let setFile: (file: any) => void;
	export let allFiles = [];

	function formatSize(bytes: number) {
		return (bytes / 1_000_000).toFixed(1);
	}
	function formatDate(dateStr: string) {
		const d = new Date(dateStr);
		const day = String(d.getDate()).padStart(2, '0');
		const month = String(d.getMonth() + 1).padStart(2, '0');
		const year = d.getFullYear();
		const time = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
		return `${day}.${month}.${year} at ${time}`;
	}
</script>

<div class="modal">
	<h2 class="title">Uploaded datasets</h2>
	<table class="file-table">
		<thead>
			<tr>
				<th style="padding-left: 24px">File name</th>
				<th>Format</th>
				<th>Headers</th>
				<th>Lines</th>
				<th>Size, Mb</th>
				<th>Date uploaded</th>
				<th></th>
			</tr>
		</thead>
		<tbody>
			{#each allFiles as file}
				<tr>
					<td style="max-width: 420px; padding-left: 24px">{file.filename}</td>
					<td>
						<span class="tag {file.filename?.split('.')?.pop()?.toUpperCase()}"
							>{file.filename?.split('.')?.pop()?.toUpperCase()}</span
						>
					</td>
					<td>{''}</td>
					<td>{''}</td>
					<td>{formatSize(file.meta.size)}</td>
					<td>{formatDate(file.created_at)}</td>
					<td>
						<!-- {#if file.showUpload} -->
						<button
							class="upload-btn"
							on:click={() => {
								setFile(file);
							}}>Upload</button
						>
						<!-- {/if} -->
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
	<div class="footer">
		<button class="cancel-btn" on:click={handleClose}>Cancel</button>
	</div>
</div>

<style>
	.modal {
		background: #fff;

		border-radius: 12px;
		width: 100%;
		margin: auto;
		font-family: system-ui, sans-serif;
	}

	.title {
		padding: 24px;
		font-size: 17px;
		font-weight: 600;
		margin-bottom: 1rem;
		border-bottom: 1px solid rgba(235, 239, 242, 1);
	}

	.file-table {
		padding: 24px;
		width: 100%;
		border-collapse: collapse;
	}

	.file-table th,
	.file-table td {
		padding: 16px 20px;
		text-align: left;
		border-bottom: 1px solid #e6e6e6;
		font-size: 14px;
		color: rgba(40, 43, 45, 1);
		vertical-align: middle;
	}
	.file-table tr:hover {
		background-color: rgba(245, 245, 245, 1);
	}
	.file-table tr:hover .upload-btn {
		opacity: 1; /* visible when row is hovered */
		background-color: rgba(49, 152, 246, 1); /* optional: change bg on hover */
	}

	.file-table th {
		color: rgba(128, 128, 128, 1);
		font-weight: 600;
		font-size: 12px;
	}

	.tag {
		display: inline-block;
		padding: 4px 10px;
		border-radius: 6px;
		font-size: 12px;
		font-weight: 600;
		text-transform: uppercase;
		color: #555;
		border: 1px solid #999;
	}

	.tag.XLSX {
		background-color: rgba(2, 214, 99, 0.1);
		color: rgba(2, 214, 99, 1);
		border: 1px solid rgba(2, 214, 99, 0.2);
	}

	.tag.CSV {
		background-color: rgba(155, 81, 224, 0.1);
		color: rgba(155, 81, 224, 1);
		border: 1px solid rgba(155, 81, 224, 0.2);
	}

	.upload-btn {
		background-color: rgba(49, 152, 246, 1);
		color: white;
		opacity: 0;
		padding: 6px 14px;
		border: none;
		border-radius: 4px;
		font-size: 14px;
		cursor: pointer;
	}

	.upload-btn:hover {
		opacity: 1;
		background-color: rgba(49, 152, 246, 1);
	}

	.footer {
		margin-top: 1.5rem;
		text-align: right;
	}

	.cancel-btn {
		background: #fff;
		border: 1px solid #ccc;
		color: #333;
		padding: 6px 14px;
		border-radius: 6px;
		cursor: pointer;
	}

	.cancel-btn:hover {
		background-color: #f2f2f2;
	}
</style>
