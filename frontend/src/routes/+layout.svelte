<script lang="ts">
	import '../app.css';

	const navItems = [
		{ href: '/', label: 'Dashboard', icon: '◉' },
		{ href: '/server', label: 'Server', icon: '▣' },
		{ href: '/monitor', label: 'Monitor', icon: '◎' },
		{ href: '/accounts', label: 'Accounts', icon: '👤' },
		{ href: '/bots', label: 'Bots', icon: '⚔' },
		{ href: '/memories', label: 'Memories', icon: '◈' },
		{ href: '/config', label: 'Config', icon: '⚙' },
		{ href: '/console', label: 'Console', icon: '▸' }
	];
</script>

<div class="layout">
	<aside class="sidebar">
		<div class="logo">
			<span class="logo-icon">◉</span>
			<span class="logo-text">CEREBRO</span>
		</div>
		<nav>
			{#each navItems as item}
				<a href={item.href} class="nav-item">
					<span class="nav-icon">{item.icon}</span>
					<span>{item.label}</span>
				</a>
			{/each}
		</nav>
		<div class="sidebar-footer">
			<span class="version">v1.0.0</span>
		</div>
	</aside>
	<main class="content">
		<slot />
	</main>
</div>

<style>
	.layout {
		display: flex;
		min-height: 100vh;
	}

	.sidebar {
		width: 220px;
		background: var(--bg-card);
		border-right: 1px solid var(--border);
		display: flex;
		flex-direction: column;
		padding: 1rem 0;
	}

	.logo {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem 1.5rem 1.5rem;
		border-bottom: 1px solid var(--border);
		margin-bottom: 1rem;
	}

	.logo-icon {
		font-size: 1.5rem;
		color: var(--accent);
	}

	.logo-text {
		font-size: 1.25rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		color: var(--text);
	}

	nav {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		padding: 0 0.75rem;
	}

	.nav-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		border-radius: 8px;
		color: var(--text-muted);
		transition: all 0.2s;
	}

	.nav-item:hover {
		background: var(--bg-card-hover);
		color: var(--text);
	}

	.nav-icon {
		font-size: 1rem;
	}

	.sidebar-footer {
		padding: 1rem 1.5rem;
		border-top: 1px solid var(--border);
	}

	.version {
		font-size: 0.75rem;
		color: var(--text-muted);
	}

	.content {
		flex: 1;
		padding: 2rem;
		overflow-y: auto;
	}
</style>
