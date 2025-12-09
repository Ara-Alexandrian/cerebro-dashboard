<script lang="ts">
	import { browser } from '$app/environment';
	import {
		getServerStatus,
		restartServer,
		stopServer,
		startServer,
		getServerLogs,
		sendServerCommand,
		getBotsStatus,
		reloadBotsConfig
	} from '$lib/api';

	// Server state
	let serverStatus: {
		worldserver: string;
		authserver: string;
		soap: string;
		host: string;
	} | null = $state(null);
	let serverLogs = $state('');
	let isLoading = $state(false);
	let statusMessage = $state('');
	let statusType: 'success' | 'error' | '' = $state('');

	// Bot control state
	let botsStatus = $state('');

	// GM Command state
	let gmCommand = $state('');
	let commandHistory: Array<{ command: string; result: string; success: boolean }> = $state([]);

	// Refresh interval
	let refreshInterval: ReturnType<typeof setInterval> | null = $state(null);
	let initialized = $state(false);

	$effect(() => {
		if (browser && !initialized) {
			initialized = true;
			loadServerStatus();
			loadServerLogs();
			loadBotsStatus();

			// Auto-refresh status every 10 seconds
			refreshInterval = setInterval(() => {
				loadServerStatus();
			}, 10000);
		}

		return () => {
			if (refreshInterval) clearInterval(refreshInterval);
		};
	});

	async function loadServerStatus() {
		try {
			serverStatus = await getServerStatus();
		} catch (e) {
			console.error('Failed to load server status:', e);
		}
	}

	async function loadServerLogs() {
		try {
			const result = await getServerLogs(200);
			if (result.success) {
				serverLogs = result.logs;
			}
		} catch (e) {
			console.error('Failed to load logs:', e);
		}
	}

	async function loadBotsStatus() {
		try {
			const result = await getBotsStatus();
			if (result.success && result.result) {
				botsStatus = result.result;
			}
		} catch (e) {
			console.error('Failed to load bots status:', e);
		}
	}

	function showMessage(message: string, type: 'success' | 'error') {
		statusMessage = message;
		statusType = type;
		setTimeout(() => {
			statusMessage = '';
			statusType = '';
		}, 5000);
	}

	async function handleRestart() {
		if (!confirm('Are you sure you want to restart the server? All players will be disconnected.')) {
			return;
		}
		isLoading = true;
		try {
			const result = await restartServer();
			if (result.success) {
				showMessage('Server restart initiated', 'success');
			} else {
				showMessage(result.error || 'Restart failed', 'error');
			}
		} catch (e) {
			showMessage('Failed to restart server', 'error');
		} finally {
			isLoading = false;
			setTimeout(loadServerStatus, 5000);
		}
	}

	async function handleStop() {
		if (!confirm('Are you sure you want to stop the server?')) {
			return;
		}
		isLoading = true;
		try {
			const result = await stopServer();
			if (result.success) {
				showMessage('Server stopped', 'success');
			} else {
				showMessage(result.error || 'Stop failed', 'error');
			}
		} catch (e) {
			showMessage('Failed to stop server', 'error');
		} finally {
			isLoading = false;
			setTimeout(loadServerStatus, 2000);
		}
	}

	async function handleStart() {
		isLoading = true;
		try {
			const result = await startServer();
			if (result.success) {
				showMessage('Server started', 'success');
			} else {
				showMessage(result.error || 'Start failed', 'error');
			}
		} catch (e) {
			showMessage('Failed to start server', 'error');
		} finally {
			isLoading = false;
			setTimeout(loadServerStatus, 5000);
		}
	}

	async function handleSendCommand() {
		if (!gmCommand.trim()) return;

		const cmd = gmCommand.trim();
		gmCommand = '';

		try {
			const result = await sendServerCommand(cmd);
			commandHistory = [
				{
					command: cmd,
					result: result.result || result.error || 'No response',
					success: result.success
				},
				...commandHistory.slice(0, 49)
			];
		} catch (e) {
			commandHistory = [
				{
					command: cmd,
					result: 'Failed to send command',
					success: false
				},
				...commandHistory.slice(0, 49)
			];
		}
	}

	async function handleReloadConfig() {
		try {
			const result = await reloadBotsConfig();
			if (result.success) {
				showMessage('Config reloaded', 'success');
			} else {
				showMessage(result.error || 'Failed to reload config', 'error');
			}
		} catch (e) {
			showMessage('Failed to reload config', 'error');
		}
	}

	function getStatusClass(status: string): string {
		if (status === 'running' || status === 'available') return 'status-ok';
		if (status === 'stopped' || status === 'unavailable') return 'status-error';
		return 'status-unknown';
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			handleSendCommand();
		}
	}
</script>

<svelte:head>
	<title>Server Control - Cerebro</title>
</svelte:head>

<div class="page">
	<header class="page-header">
		<h1>Server Control</h1>
		<p class="subtitle">Manage AzerothCore server and PlayerBots</p>
	</header>

	{#if statusMessage}
		<div class="toast {statusType}">{statusMessage}</div>
	{/if}

	<div class="grid">
		<!-- Server Status Card -->
		<section class="card status-card">
			<h2>Server Status</h2>
			{#if serverStatus}
				<div class="status-grid">
					<div class="status-item">
						<span class="status-label">WorldServer</span>
						<span class="status-value {getStatusClass(serverStatus.worldserver)}">
							{serverStatus.worldserver}
						</span>
					</div>
					<div class="status-item">
						<span class="status-label">AuthServer</span>
						<span class="status-value {getStatusClass(serverStatus.authserver)}">
							{serverStatus.authserver}
						</span>
					</div>
					<div class="status-item">
						<span class="status-label">SOAP</span>
						<span class="status-value {getStatusClass(serverStatus.soap)}">
							{serverStatus.soap}
						</span>
					</div>
					<div class="status-item">
						<span class="status-label">Host</span>
						<span class="status-value">{serverStatus.host}</span>
					</div>
				</div>
			{:else}
				<p class="loading">Loading status...</p>
			{/if}

			<div class="button-row">
				<button
					class="btn btn-success"
					on:click={handleStart}
					disabled={isLoading || serverStatus?.worldserver === 'running'}
				>
					Start
				</button>
				<button
					class="btn btn-warning"
					on:click={handleRestart}
					disabled={isLoading}
				>
					Restart
				</button>
				<button
					class="btn btn-danger"
					on:click={handleStop}
					disabled={isLoading || serverStatus?.worldserver === 'stopped'}
				>
					Stop
				</button>
				<button class="btn btn-secondary" on:click={loadServerStatus} disabled={isLoading}>
					Refresh
				</button>
			</div>
		</section>

		<!-- PlayerBots Control Card -->
		<section class="card bots-card">
			<h2>PlayerBots Status</h2>

			<div class="bots-status">
				<pre>{botsStatus || 'No bot status available'}</pre>
			</div>

			<p class="info-text">
				Bot count is configured in playerbots.conf. Use the Config page to modify settings, then reload.
			</p>

			<div class="button-row">
				<button class="btn btn-secondary" on:click={handleReloadConfig}>
					Reload Config
				</button>
				<button class="btn btn-secondary" on:click={loadBotsStatus}>
					Refresh Status
				</button>
			</div>
		</section>

		<!-- GM Command Console -->
		<section class="card command-card">
			<h2>GM Commands</h2>

			<div class="command-form">
				<input
					type="text"
					bind:value={gmCommand}
					on:keydown={handleKeydown}
					placeholder="Enter GM command (e.g., .server info)"
					class="command-input"
				/>
				<button class="btn btn-primary" on:click={handleSendCommand}>Send</button>
			</div>

			<div class="command-history">
				{#each commandHistory as entry}
					<div class="command-entry {entry.success ? 'success' : 'error'}">
						<div class="command-cmd">&gt; {entry.command}</div>
						<pre class="command-result">{entry.result}</pre>
					</div>
				{/each}
				{#if commandHistory.length === 0}
					<p class="empty">No commands executed yet</p>
				{/if}
			</div>
		</section>

		<!-- Server Logs -->
		<section class="card logs-card">
			<h2>
				Server Logs
				<button class="btn btn-small btn-secondary" on:click={loadServerLogs}>
					Refresh
				</button>
			</h2>
			<pre class="logs">{serverLogs || 'No logs available'}</pre>
		</section>
	</div>
</div>

<style>
	.page {
		max-width: 1600px;
		margin: 0 auto;
	}

	.page-header {
		margin-bottom: 2rem;
	}

	.page-header h1 {
		font-size: 1.75rem;
		margin-bottom: 0.5rem;
	}

	.subtitle {
		color: var(--text-muted);
	}

	.toast {
		padding: 1rem;
		border-radius: 8px;
		margin-bottom: 1rem;
		font-weight: 500;
	}

	.toast.success {
		background: rgba(34, 197, 94, 0.2);
		border: 1px solid rgba(34, 197, 94, 0.4);
		color: #22c55e;
	}

	.toast.error {
		background: rgba(239, 68, 68, 0.2);
		border: 1px solid rgba(239, 68, 68, 0.4);
		color: #ef4444;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1.5rem;
	}

	.card {
		background: var(--bg-card);
		border: 1px solid var(--border);
		border-radius: 12px;
		padding: 1.5rem;
	}

	.card h2 {
		font-size: 1.125rem;
		margin-bottom: 1rem;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}

	.status-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1rem;
		margin-bottom: 1.5rem;
	}

	.status-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.status-label {
		font-size: 0.875rem;
		color: var(--text-muted);
	}

	.status-value {
		font-weight: 600;
		text-transform: capitalize;
	}

	.status-ok {
		color: #22c55e;
	}

	.status-error {
		color: #ef4444;
	}

	.status-unknown {
		color: var(--text-muted);
	}

	.button-row {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.btn {
		padding: 0.625rem 1rem;
		border-radius: 6px;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
		border: none;
	}

	.btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-primary {
		background: var(--accent);
		color: white;
	}

	.btn-primary:hover:not(:disabled) {
		background: var(--accent-hover);
	}

	.btn-success {
		background: #22c55e;
		color: white;
	}

	.btn-success:hover:not(:disabled) {
		background: #16a34a;
	}

	.btn-warning {
		background: #eab308;
		color: black;
	}

	.btn-warning:hover:not(:disabled) {
		background: #ca8a04;
	}

	.btn-danger {
		background: #ef4444;
		color: white;
	}

	.btn-danger:hover:not(:disabled) {
		background: #dc2626;
	}

	.btn-secondary {
		background: var(--bg-card-hover);
		color: var(--text);
	}

	.btn-secondary:hover:not(:disabled) {
		background: var(--border);
	}

	.btn-small {
		padding: 0.375rem 0.75rem;
		font-size: 0.875rem;
	}

	.info-text {
		font-size: 0.875rem;
		color: var(--text-muted);
		margin-bottom: 1rem;
	}

	.bots-status {
		background: var(--bg);
		border-radius: 6px;
		padding: 1rem;
		margin-bottom: 1rem;
		max-height: 150px;
		overflow-y: auto;
	}

	.bots-status pre {
		font-size: 0.875rem;
		white-space: pre-wrap;
		word-break: break-word;
	}

	.command-form {
		display: flex;
		gap: 0.75rem;
		margin-bottom: 1rem;
	}

	.command-input {
		flex: 1;
		padding: 0.75rem;
		border-radius: 6px;
		border: 1px solid var(--border);
		background: var(--bg);
		color: var(--text);
		font-family: monospace;
	}

	.command-history {
		max-height: 300px;
		overflow-y: auto;
	}

	.command-entry {
		padding: 0.75rem;
		border-radius: 6px;
		margin-bottom: 0.5rem;
		background: var(--bg);
	}

	.command-entry.success {
		border-left: 3px solid #22c55e;
	}

	.command-entry.error {
		border-left: 3px solid #ef4444;
	}

	.command-cmd {
		font-family: monospace;
		color: var(--accent);
		margin-bottom: 0.5rem;
	}

	.command-result {
		font-size: 0.875rem;
		white-space: pre-wrap;
		word-break: break-word;
	}

	.empty {
		color: var(--text-muted);
		text-align: center;
		padding: 2rem;
	}

	.loading {
		color: var(--text-muted);
	}

	.logs-card {
		grid-column: span 2;
	}

	.logs {
		background: var(--bg);
		border-radius: 6px;
		padding: 1rem;
		max-height: 400px;
		overflow-y: auto;
		font-size: 0.75rem;
		line-height: 1.5;
		white-space: pre-wrap;
		word-break: break-word;
	}

	@media (max-width: 1024px) {
		.grid {
			grid-template-columns: 1fr;
		}

		.logs-card {
			grid-column: span 1;
		}
	}
</style>
