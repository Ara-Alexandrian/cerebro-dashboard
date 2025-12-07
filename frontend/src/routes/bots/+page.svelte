<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { getPersonalities, createPersonality, updatePersonality, deletePersonality, type Personality } from '$lib/api';

	let personalities: Personality[] = [];
	let loading = true;
	let showForm = false;
	let editingId: number | null = null;

	// Form fields
	let name = '';
	let botClass = 'warrior';
	let archetype = 'dps';
	let systemPrompt = '';
	let formError = '';

	const classes = ['warrior', 'paladin', 'hunter', 'rogue', 'priest', 'shaman', 'mage', 'warlock', 'druid', 'death_knight'];
	const archetypes = ['tank', 'healer', 'dps'];

	onMount(async () => {
		if (browser) {
			await refresh();
		}
	});

	async function refresh() {
		loading = true;
		try {
			const data = await getPersonalities();
			personalities = data.personalities;
		} catch (e) {
			console.error('Failed to load personalities:', e);
		} finally {
			loading = false;
		}
	}

	async function handleSubmit() {
		formError = '';
		try {
			if (editingId) {
				await updatePersonality(editingId, {
					name,
					class_: botClass,
					archetype,
					system_prompt: systemPrompt
				});
			} else {
				await createPersonality({
					name,
					class_: botClass,
					archetype,
					traits: {},
					system_prompt: systemPrompt
				});
			}
			resetForm();
			await refresh();
		} catch (e) {
			formError = e instanceof Error ? e.message : 'Failed to save personality';
		}
	}

	function startEdit(bot: Personality) {
		editingId = bot.id;
		name = bot.name;
		botClass = bot.class;
		archetype = bot.archetype;
		systemPrompt = bot.system_prompt || '';
		showForm = true;
		formError = '';
	}

	function resetForm() {
		showForm = false;
		editingId = null;
		name = '';
		botClass = 'warrior';
		archetype = 'dps';
		systemPrompt = '';
		formError = '';
	}

	async function handleDelete(id: number) {
		if (!confirm('Delete this personality?')) return;
		try {
			await deletePersonality(id);
			await refresh();
		} catch (e) {
			console.error('Failed to delete:', e);
		}
	}

	function getClassColor(cls: string): string {
		const colors: Record<string, string> = {
			warrior: '#C79C6E',
			paladin: '#F58CBA',
			hunter: '#ABD473',
			rogue: '#FFF569',
			priest: '#FFFFFF',
			shaman: '#0070DE',
			mage: '#69CCF0',
			warlock: '#9482C9',
			druid: '#FF7D0A',
			death_knight: '#C41F3B'
		};
		return colors[cls] || '#888888';
	}
</script>

<div class="bots-page">
	<header>
		<h1>Bot Personalities</h1>
		<button class="primary" on:click={() => showForm ? resetForm() : (showForm = true)}>
			{showForm ? 'Cancel' : '+ New Personality'}
		</button>
	</header>

	{#if showForm}
		<div class="card form-card">
			<h2>{editingId ? 'Edit Personality' : 'Create Personality'}</h2>
			<form on:submit|preventDefault={handleSubmit}>
				<div class="form-row">
					<label>
						<span>Name</span>
						<input type="text" bind:value={name} required placeholder="Thorgrim" />
					</label>
					<label>
						<span>Class</span>
						<select bind:value={botClass}>
							{#each classes as cls}
								<option value={cls}>{cls.replace('_', ' ')}</option>
							{/each}
						</select>
					</label>
					<label>
						<span>Archetype</span>
						<select bind:value={archetype}>
							{#each archetypes as arch}
								<option value={arch}>{arch}</option>
							{/each}
						</select>
					</label>
				</div>
				<label class="full-width">
					<span>System Prompt</span>
					<textarea
						bind:value={systemPrompt}
						rows="4"
						placeholder="You are a gruff dwarven warrior who speaks in short, direct sentences..."
					></textarea>
				</label>
				{#if formError}
					<div class="form-error">{formError}</div>
				{/if}
				<div class="form-actions">
					<button type="submit" class="primary">{editingId ? 'Save Changes' : 'Create'}</button>
				</div>
			</form>
		</div>
	{/if}

	{#if loading}
		<div class="loading">Loading...</div>
	{:else if personalities.length === 0}
		<div class="empty card">
			<p>No personalities created yet.</p>
			<p>Create your first AI companion!</p>
		</div>
	{:else}
		<div class="personality-grid">
			{#each personalities as bot}
				<div class="card personality-card">
					<div class="personality-header">
						<span class="personality-name" style="color: {getClassColor(bot.class)}">{bot.name}</span>
						<div class="card-actions">
							<button class="edit-btn" on:click={() => startEdit(bot)} title="Edit">✎</button>
							<button class="delete-btn" on:click={() => handleDelete(bot.id)} title="Delete">×</button>
						</div>
					</div>
					<div class="personality-meta">
						<span class="class-badge" style="background: {getClassColor(bot.class)}20; color: {getClassColor(bot.class)}">
							{bot.class}
						</span>
						<span class="archetype-badge">{bot.archetype}</span>
					</div>
					{#if bot.system_prompt}
						<p class="personality-prompt">{bot.system_prompt.slice(0, 100)}...</p>
					{/if}
					<div class="personality-footer">
						<span class="created">Created: {new Date(bot.created_at).toLocaleDateString()}</span>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.bots-page {
		max-width: 1000px;
	}

	header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
	}

	h1 {
		font-size: 2rem;
		font-weight: 600;
	}

	h2 {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 1.5rem;
		color: var(--text-muted);
		text-transform: uppercase;
	}

	.form-card {
		margin-bottom: 2rem;
	}

	.form-row {
		display: grid;
		grid-template-columns: 2fr 1fr 1fr;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	label {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	label span {
		font-size: 0.75rem;
		color: var(--text-muted);
		text-transform: uppercase;
	}

	label.full-width {
		margin-bottom: 1rem;
	}

	textarea {
		resize: vertical;
		min-height: 80px;
	}

	.form-error {
		color: var(--error);
		margin-bottom: 1rem;
	}

	.form-actions {
		display: flex;
		justify-content: flex-end;
	}

	.loading, .empty {
		text-align: center;
		padding: 2rem;
		color: var(--text-muted);
	}

	.personality-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1.5rem;
	}

	.personality-card {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.personality-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.personality-name {
		font-size: 1.25rem;
		font-weight: 600;
	}

	.card-actions {
		display: flex;
		gap: 0.25rem;
	}

	.edit-btn, .delete-btn {
		background: none;
		color: var(--text-muted);
		font-size: 1.25rem;
		padding: 0;
		width: 2rem;
		height: 2rem;
		border-radius: 4px;
		transition: all 0.15s;
	}

	.edit-btn:hover {
		color: var(--accent);
		background: var(--bg-dark);
	}

	.delete-btn:hover {
		color: var(--error);
		background: var(--bg-dark);
	}

	.personality-meta {
		display: flex;
		gap: 0.5rem;
	}

	.class-badge, .archetype-badge {
		font-size: 0.75rem;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		text-transform: capitalize;
	}

	.archetype-badge {
		background: var(--bg-dark);
		color: var(--text-muted);
	}

	.personality-prompt {
		font-size: 0.875rem;
		color: var(--text-muted);
		line-height: 1.5;
	}

	.personality-footer {
		margin-top: auto;
		padding-top: 0.75rem;
		border-top: 1px solid var(--border);
	}

	.created {
		font-size: 0.75rem;
		color: var(--text-muted);
	}
</style>
