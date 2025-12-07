<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { getHealth, getStats, getPersonalities } from '$lib/api';

	let health: Awaited<ReturnType<typeof getHealth>> | null = null;
	let stats: Awaited<ReturnType<typeof getStats>> | null = null;
	let personalities: Awaited<ReturnType<typeof getPersonalities>> | null = null;
	let loading = true;
	let refreshing = false;
	let error = '';
	let lastUpdated = '';
	let interval: ReturnType<typeof setInterval>;

	async function refresh(showLoading = false) {
		if (showLoading) loading = true;
		refreshing = true;
		error = '';
		try {
			[health, stats, personalities] = await Promise.all([
				getHealth(),
				getStats(),
				getPersonalities()
			]);
			lastUpdated = new Date().toLocaleTimeString();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load data';
		} finally {
			loading = false;
			refreshing = false;
		}
	}

	onMount(() => {
		if (browser) {
			refresh(true);
			// Auto-refresh every 30 seconds
			interval = setInterval(() => refresh(false), 30000);
		}
	});

	onDestroy(() => {
		if (interval) clearInterval(interval);
	});

	function getStatusClass(status: string | undefined) {
		if (!status) return '';
		if (status === 'healthy' || status === 'running') return 'healthy';
		if (status === 'degraded') return 'degraded';
		return 'unhealthy';
	}
</script>

<div class="dashboard">
	<header>
		<div class="header-left">
			<h1>Cerebro Dashboard</h1>
			<p class="subtitle">AzerothCore AI Buddy System</p>
		</div>
		<div class="header-right">
			{#if lastUpdated}
				<span class="last-updated">Updated: {lastUpdated}</span>
			{/if}
			<button class="refresh-btn" on:click={() => refresh(false)} disabled={refreshing}>
				<span class:spinning={refreshing}>↻</span>
			</button>
		</div>
	</header>

	{#if loading}
		<div class="loading">Loading...</div>
	{:else if error}
		<div class="error">{error}</div>
	{:else}
		<div class="grid">
			<!-- System Status -->
			<div class="card status-card">
				<h2>System Status</h2>
				<div class="status-grid">
					<div class="status-item">
						<span class="status-dot {getStatusClass(health?.azerothcore?.worldserver)}"></span>
						<span class="status-label">WorldServer</span>
						<span class="status-value">{health?.azerothcore?.worldserver ?? 'unknown'}</span>
					</div>
					<div class="status-item">
						<span class="status-dot {getStatusClass(health?.azerothcore?.authserver)}"></span>
						<span class="status-label">AuthServer</span>
						<span class="status-value">{health?.azerothcore?.authserver ?? 'unknown'}</span>
					</div>
					<div class="status-item">
						<span class="status-dot {getStatusClass(health?.vllm?.status)}"></span>
						<span class="status-label">vLLM</span>
						<span class="status-value">{health?.vllm?.status ?? 'unknown'}</span>
					</div>
					<div class="status-item">
						<span class="status-dot {getStatusClass(health?.redis?.status)}"></span>
						<span class="status-label">Redis</span>
						<span class="status-value">{health?.redis?.status ?? 'unknown'}</span>
					</div>
					<div class="status-item">
						<span class="status-dot {getStatusClass(health?.postgresql?.status)}"></span>
						<span class="status-label">PostgreSQL</span>
						<span class="status-value">{health?.postgresql?.status ?? 'unknown'}</span>
					</div>
				</div>
				<div class="overall-status">
					<span>Overall:</span>
					<span class="status-badge {getStatusClass(health?.overall)}">{health?.overall ?? 'unknown'}</span>
				</div>
			</div>

			<!-- Quick Stats -->
			<div class="card stats-card">
				<h2>Quick Stats</h2>
				<div class="stat-grid">
					<div class="stat">
						<span class="stat-value">{stats?.active_bots ?? 0}</span>
						<span class="stat-label">Active Bots</span>
					</div>
					<div class="stat">
						<span class="stat-value">{personalities?.personalities?.length ?? 0}</span>
						<span class="stat-label">Personalities</span>
					</div>
				</div>
			</div>

			<!-- Bot Personalities -->
			<div class="card personalities-card">
				<h2>Bot Personalities</h2>
				{#if personalities?.personalities?.length}
					<div class="personality-list">
						{#each personalities.personalities.slice(0, 5) as bot}
							<div class="personality-item">
								<span class="personality-name">{bot.name}</span>
								<span class="personality-class">{bot.class} ({bot.archetype})</span>
							</div>
						{/each}
					</div>
					<a href="/bots" class="view-all">View all →</a>
				{:else}
					<p class="empty">No personalities created yet</p>
					<a href="/bots" class="view-all">Create one →</a>
				{/if}
			</div>

			<!-- Quick Actions -->
			<div class="card actions-card">
				<h2>Quick Actions</h2>
				<div class="action-buttons">
					<a href="/bots" class="action-btn">
						<span class="action-icon">+</span>
						<span>New Personality</span>
					</a>
					<a href="/console" class="action-btn">
						<span class="action-icon">▸</span>
						<span>GM Console</span>
					</a>
					<a href="/monitor" class="action-btn">
						<span class="action-icon">◎</span>
						<span>Monitor</span>
					</a>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.dashboard {
		max-width: 1200px;
	}

	header {
		margin-bottom: 2rem;
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
	}

	h1 {
		font-size: 2rem;
		font-weight: 600;
		margin-bottom: 0.25rem;
	}

	.subtitle {
		color: var(--text-muted);
	}

	.header-right {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.last-updated {
		font-size: 0.75rem;
		color: var(--text-muted);
	}

	.refresh-btn {
		width: 36px;
		height: 36px;
		border-radius: 8px;
		background: var(--bg-card);
		border: 1px solid var(--border);
		color: var(--text-muted);
		font-size: 1.25rem;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: all 0.15s;
	}

	.refresh-btn:hover:not(:disabled) {
		color: var(--accent);
		border-color: var(--accent);
	}

	.refresh-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.spinning {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	h2 {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 1rem;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1.5rem;
	}

	.loading, .error {
		padding: 2rem;
		text-align: center;
		color: var(--text-muted);
	}

	.error {
		color: var(--error);
	}

	/* Status Card */
	.status-grid {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.status-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.status-label {
		flex: 1;
	}

	.status-value {
		color: var(--text-muted);
		font-size: 0.875rem;
	}

	.overall-status {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid var(--border);
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.status-badge {
		padding: 0.25rem 0.75rem;
		border-radius: 9999px;
		font-size: 0.75rem;
		font-weight: 500;
		text-transform: uppercase;
	}

	.status-badge.healthy {
		background: rgba(34, 197, 94, 0.2);
		color: var(--success);
	}

	.status-badge.degraded {
		background: rgba(234, 179, 8, 0.2);
		color: var(--warning);
	}

	.status-badge.unhealthy {
		background: rgba(239, 68, 68, 0.2);
		color: var(--error);
	}

	/* Stats Card */
	.stat-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1rem;
	}

	.stat {
		text-align: center;
		padding: 1rem;
		background: var(--bg-dark);
		border-radius: 8px;
	}

	.stat-value {
		display: block;
		font-size: 2rem;
		font-weight: 700;
		color: var(--accent);
	}

	.stat-label {
		font-size: 0.75rem;
		color: var(--text-muted);
		text-transform: uppercase;
	}

	/* Personalities Card */
	.personality-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.personality-item {
		display: flex;
		justify-content: space-between;
		padding: 0.5rem 0;
		border-bottom: 1px solid var(--border);
	}

	.personality-name {
		font-weight: 500;
	}

	.personality-class {
		color: var(--text-muted);
		font-size: 0.875rem;
	}

	.view-all {
		display: block;
		margin-top: 1rem;
		font-size: 0.875rem;
	}

	.empty {
		color: var(--text-muted);
		font-style: italic;
	}

	/* Actions Card */
	.action-buttons {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.action-btn {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		background: var(--bg-dark);
		border-radius: 8px;
		color: var(--text);
		transition: all 0.2s;
	}

	.action-btn:hover {
		background: var(--bg-card-hover);
		color: var(--accent);
	}

	.action-icon {
		width: 1.5rem;
		text-align: center;
		color: var(--accent);
	}
</style>
