<script lang="ts">
	import { browser } from '$app/environment';
	import { getConfigs, getConfig } from '$lib/api';

	let configs: Array<{ name: string; path: string; size: number }> = $state([]);
	let selectedConfig: string | null = $state(null);
	let configContent = $state('');
	let loading = $state(true);
	let saving = $state(false);
	let initialized = $state(false);

	$effect(() => {
		if (browser && !initialized) {
			initialized = true;
			loadConfigs();
		}
	});

	async function loadConfigs() {
		try {
			const data = await getConfigs();
			configs = data.configs;
		} catch (e) {
			console.error('Failed to load configs:', e);
		} finally {
			loading = false;
		}
	}

	async function loadConfig(name: string) {
		selectedConfig = name;
		try {
			const data = await getConfig(name);
			configContent = data.content;
		} catch (e) {
			configContent = `Error loading config: ${e instanceof Error ? e.message : 'Unknown'}`;
		}
	}

	async function saveConfig() {
		if (!selectedConfig) return;
		saving = true;
		try {
			await fetch(`/api/config/files/${selectedConfig}`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ content: configContent })
			});
			alert('Config saved! Restart the server to apply changes.');
		} catch (e) {
			alert(`Failed to save: ${e instanceof Error ? e.message : 'Unknown error'}`);
		} finally {
			saving = false;
		}
	}

	function formatSize(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		return `${(bytes / 1024).toFixed(1)} KB`;
	}
</script>

<div class="config-page">
	<h1>Configuration</h1>

	<div class="layout">
		<aside class="file-list card">
			<h2>Config Files</h2>
			{#if loading}
				<p class="loading">Loading...</p>
			{:else if configs.length === 0}
				<p class="empty">No config files found</p>
			{:else}
				{#each configs as config}
					<button
						class="file-item"
						class:selected={selectedConfig === config.name}
						on:click={() => loadConfig(config.name)}
					>
						<span class="file-name">{config.name}</span>
						<span class="file-size">{formatSize(config.size)}</span>
					</button>
				{/each}
			{/if}
		</aside>

		<main class="editor card">
			{#if selectedConfig}
				<div class="editor-header">
					<h2>{selectedConfig}</h2>
					<button class="primary" on:click={saveConfig} disabled={saving}>
						{saving ? 'Saving...' : 'Save'}
					</button>
				</div>
				<textarea bind:value={configContent} spellcheck="false"></textarea>
			{:else}
				<div class="no-selection">
					<p>Select a config file to edit</p>
				</div>
			{/if}
		</main>
	</div>
</div>

<style>
	.config-page {
		max-width: 1200px;
		height: calc(100vh - 4rem);
		display: flex;
		flex-direction: column;
	}

	h1 {
		font-size: 2rem;
		font-weight: 600;
		margin-bottom: 2rem;
	}

	h2 {
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-muted);
		text-transform: uppercase;
		margin-bottom: 1rem;
	}

	.layout {
		display: grid;
		grid-template-columns: 250px 1fr;
		gap: 1.5rem;
		flex: 1;
		min-height: 0;
	}

	.file-list {
		display: flex;
		flex-direction: column;
	}

	.file-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem;
		background: transparent;
		text-align: left;
		border-radius: 6px;
		color: var(--text);
	}

	.file-item:hover {
		background: var(--bg-card-hover);
	}

	.file-item.selected {
		background: var(--accent);
		color: white;
	}

	.file-name {
		font-size: 0.875rem;
	}

	.file-size {
		font-size: 0.75rem;
		opacity: 0.7;
	}

	.editor {
		display: flex;
		flex-direction: column;
		min-height: 0;
	}

	.editor-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.editor-header h2 {
		margin: 0;
	}

	.editor textarea {
		flex: 1;
		font-family: 'Consolas', 'Monaco', monospace;
		font-size: 0.8125rem;
		line-height: 1.5;
		resize: none;
		padding: 1rem;
		background: var(--bg-dark);
		border: 1px solid var(--border);
		border-radius: 8px;
	}

	.no-selection {
		display: flex;
		align-items: center;
		justify-content: center;
		flex: 1;
		color: var(--text-muted);
	}

	.loading, .empty {
		color: var(--text-muted);
		padding: 1rem 0;
	}
</style>
