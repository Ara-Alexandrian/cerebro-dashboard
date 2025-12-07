<script lang="ts">
	import { browser } from '$app/environment';
	import { getHealth, getVllmStatus } from '$lib/api';

	let health: Awaited<ReturnType<typeof getHealth>> | null = $state(null);
	let vllmStatus: Awaited<ReturnType<typeof getVllmStatus>> | null = $state(null);
	let loading = $state(true);

	async function refresh() {
		try {
			const [h, v] = await Promise.all([getHealth(), getVllmStatus()]);
			health = h;
			vllmStatus = v;
		} catch (e) {
			console.error('Failed to refresh:', e);
		}
	}

	$effect(() => {
		if (!browser) return;

		refresh().then(() => {
			loading = false;
		});

		const interval = setInterval(refresh, 5000);

		return () => {
			clearInterval(interval);
		};
	});

	function getStatusClass(status: string | undefined) {
		if (!status) return 'unknown';
		if (status === 'healthy' || status === 'running') return 'healthy';
		if (status === 'degraded') return 'degraded';
		return 'unhealthy';
	}
</script>

<div class="monitor">
	<header>
		<h1>System Monitor</h1>
		<button class="secondary" onclick={refresh}>Refresh</button>
	</header>

	{#if loading}
		<div class="loading">Loading...</div>
	{:else}
		<div class="grid">
			<!-- AzerothCore -->
			<div class="card">
				<h2>AzerothCore</h2>
				<div class="service-status">
					<div class="service-row">
						<span class="status-dot {getStatusClass(health?.azerothcore?.worldserver)}"></span>
						<span class="service-name">WorldServer</span>
						<span class="service-info">Port 8085</span>
						<span class="status-text {getStatusClass(health?.azerothcore?.worldserver)}">
							{health?.azerothcore?.worldserver ?? 'unknown'}
						</span>
					</div>
					<div class="service-row">
						<span class="status-dot {getStatusClass(health?.azerothcore?.authserver)}"></span>
						<span class="service-name">AuthServer</span>
						<span class="service-info">Port 3724</span>
						<span class="status-text {getStatusClass(health?.azerothcore?.authserver)}">
							{health?.azerothcore?.authserver ?? 'unknown'}
						</span>
					</div>
				</div>
			</div>

			<!-- vLLM -->
			<div class="card">
				<h2>vLLM Server</h2>
				<div class="service-status">
					<div class="service-row">
						<span class="status-dot {getStatusClass(vllmStatus?.health?.status)}"></span>
						<span class="service-name">Inference Server</span>
						<span class="service-info">Port 8000</span>
						<span class="status-text {getStatusClass(vllmStatus?.health?.status)}">
							{vllmStatus?.health?.status ?? 'unknown'}
						</span>
					</div>
				</div>
				{#if vllmStatus?.models?.length}
					<div class="models">
						<h3>Loaded Models</h3>
						{#each vllmStatus.models as model}
							<div class="model-item">{model.id}</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Redis -->
			<div class="card">
				<h2>Redis</h2>
				<div class="service-status">
					<div class="service-row">
						<span class="status-dot {getStatusClass(health?.redis?.status)}"></span>
						<span class="service-name">Real-time State</span>
						<span class="service-info">Port 6380</span>
						<span class="status-text {getStatusClass(health?.redis?.status)}">
							{health?.redis?.status ?? 'unknown'}
						</span>
					</div>
				</div>
			</div>

			<!-- PostgreSQL -->
			<div class="card">
				<h2>PostgreSQL + pgvector</h2>
				<div class="service-status">
					<div class="service-row">
						<span class="status-dot {getStatusClass(health?.postgresql?.status)}"></span>
						<span class="service-name">Persistent Storage</span>
						<span class="service-info">Port 5433</span>
						<span class="status-text {getStatusClass(health?.postgresql?.status)}">
							{health?.postgresql?.status ?? 'unknown'}
						</span>
					</div>
				</div>
			</div>
		</div>

		<!-- Overall Status -->
		<div class="overall card">
			<div class="overall-inner">
				<span class="overall-label">Overall System Status</span>
				<span class="overall-badge {getStatusClass(health?.overall)}">
					{health?.overall ?? 'unknown'}
				</span>
			</div>
		</div>
	{/if}
</div>

<style>
	.monitor {
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
		margin-bottom: 1rem;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	h3 {
		font-size: 0.75rem;
		color: var(--text-muted);
		margin: 1rem 0 0.5rem;
		text-transform: uppercase;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1.5rem;
		margin-bottom: 1.5rem;
	}

	.loading {
		text-align: center;
		padding: 2rem;
		color: var(--text-muted);
	}

	.service-status {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.service-row {
		display: grid;
		grid-template-columns: auto 1fr auto auto;
		align-items: center;
		gap: 0.75rem;
	}

	.service-name {
		font-weight: 500;
	}

	.service-info {
		color: var(--text-muted);
		font-size: 0.75rem;
	}

	.status-text {
		font-size: 0.75rem;
		font-weight: 500;
		text-transform: uppercase;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
	}

	.status-text.healthy, .status-text.running {
		color: var(--success);
		background: rgba(34, 197, 94, 0.1);
	}

	.status-text.unhealthy, .status-text.stopped {
		color: var(--error);
		background: rgba(239, 68, 68, 0.1);
	}

	.status-text.degraded {
		color: var(--warning);
		background: rgba(234, 179, 8, 0.1);
	}

	.models {
		border-top: 1px solid var(--border);
		margin-top: 1rem;
		padding-top: 0.5rem;
	}

	.model-item {
		font-family: monospace;
		font-size: 0.75rem;
		color: var(--accent);
		padding: 0.25rem 0;
	}

	.overall {
		margin-top: 1.5rem;
	}

	.overall-inner {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.overall-label {
		font-size: 1.125rem;
		font-weight: 600;
	}

	.overall-badge {
		font-size: 1rem;
		font-weight: 600;
		text-transform: uppercase;
		padding: 0.5rem 1.5rem;
		border-radius: 9999px;
	}

	.overall-badge.healthy {
		background: rgba(34, 197, 94, 0.2);
		color: var(--success);
	}

	.overall-badge.degraded {
		background: rgba(234, 179, 8, 0.2);
		color: var(--warning);
	}

	.overall-badge.unhealthy {
		background: rgba(239, 68, 68, 0.2);
		color: var(--error);
	}
</style>
