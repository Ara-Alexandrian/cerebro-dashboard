<script lang="ts">
	import { browser } from '$app/environment';
	import { getMemories, getPersonalities, searchMemories, type Memory, type Personality } from '$lib/api';

	let memories: Memory[] = $state([]);
	let personalities: Personality[] = $state([]);
	let loading = $state(true);
	let searchQuery = $state('');
	let filterBotId: number | null = $state(null);
	let filterType: string | null = $state(null);
	let initialized = $state(false);

	const memoryTypes = ['combat', 'social', 'exploration'];

	$effect(() => {
		if (browser && !initialized) {
			initialized = true;
			loadInitialData();
		}
	});

	async function loadInitialData() {
		try {
			const [memData, botData] = await Promise.all([getMemories(), getPersonalities()]);
			memories = memData.memories;
			personalities = botData.personalities;
		} catch (e) {
			console.error('Failed to load memories:', e);
		} finally {
			loading = false;
		}
	}

	async function refresh() {
		loading = true;
		try {
			if (searchQuery.trim()) {
				const data = await searchMemories(searchQuery, filterBotId ?? undefined);
				memories = data.memories;
			} else {
				const data = await getMemories({
					bot_id: filterBotId ?? undefined,
					memory_type: filterType ?? undefined
				});
				memories = data.memories;
			}
		} catch (e) {
			console.error('Failed to refresh:', e);
		} finally {
			loading = false;
		}
	}

	function getTypeColor(type: string): string {
		const colors: Record<string, string> = {
			combat: '#ef4444',
			social: '#22c55e',
			exploration: '#3b82f6'
		};
		return colors[type] || '#888888';
	}
</script>

<div class="memories-page">
	<header>
		<h1>Memories</h1>
	</header>

	<div class="filters card">
		<div class="filter-row">
			<input
				type="text"
				placeholder="Search memories..."
				bind:value={searchQuery}
				on:input={refresh}
			/>
			<select bind:value={filterBotId} on:change={refresh}>
				<option value={null}>All Bots</option>
				{#each personalities as bot}
					<option value={bot.id}>{bot.name}</option>
				{/each}
			</select>
			<select bind:value={filterType} on:change={refresh}>
				<option value={null}>All Types</option>
				{#each memoryTypes as type}
					<option value={type}>{type}</option>
				{/each}
			</select>
		</div>
	</div>

	{#if loading}
		<div class="loading">Loading...</div>
	{:else if memories.length === 0}
		<div class="empty card">
			<p>No memories found.</p>
			<p>Memories will be created as bots interact with the world.</p>
		</div>
	{:else}
		<div class="memory-list">
			{#each memories as memory}
				<div class="card memory-item">
					<div class="memory-header">
						<span class="bot-name">{memory.bot_name ?? 'Unknown Bot'}</span>
						<span class="memory-type" style="background: {getTypeColor(memory.memory_type)}20; color: {getTypeColor(memory.memory_type)}">
							{memory.memory_type}
						</span>
						<span class="importance" title="Importance">
							{'★'.repeat(Math.round(memory.importance * 5))}{'☆'.repeat(5 - Math.round(memory.importance * 5))}
						</span>
					</div>
					<p class="memory-content">{memory.content}</p>
					<div class="memory-footer">
						<span class="timestamp">{new Date(memory.created_at).toLocaleString()}</span>
						<span class="session">Session: {memory.session_id.slice(0, 8)}...</span>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.memories-page {
		max-width: 800px;
	}

	header {
		margin-bottom: 2rem;
	}

	h1 {
		font-size: 2rem;
		font-weight: 600;
	}

	.filters {
		margin-bottom: 1.5rem;
	}

	.filter-row {
		display: flex;
		gap: 1rem;
	}

	.filter-row input {
		flex: 1;
	}

	.filter-row select {
		min-width: 120px;
	}

	.loading, .empty {
		text-align: center;
		padding: 2rem;
		color: var(--text-muted);
	}

	.memory-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.memory-item {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.memory-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.bot-name {
		font-weight: 600;
	}

	.memory-type {
		font-size: 0.75rem;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		text-transform: capitalize;
	}

	.importance {
		margin-left: auto;
		color: var(--gold);
		font-size: 0.75rem;
	}

	.memory-content {
		line-height: 1.6;
		color: var(--text);
	}

	.memory-footer {
		display: flex;
		justify-content: space-between;
		font-size: 0.75rem;
		color: var(--text-muted);
		padding-top: 0.5rem;
		border-top: 1px solid var(--border);
	}
</style>
