<script lang="ts">
	import { browser } from '$app/environment';
	import { getCommonCommands, sendGmCommand, testChat } from '$lib/api';

	let commands: Array<{ cmd: string; desc: string }> = $state([]);
	let gmCommand = $state('');
	let gmResult = $state('');
	let chatMessage = $state('');
	let chatHistory: Array<{ role: string; content: string }> = $state([]);
	let chatLoading = $state(false);
	let initialized = $state(false);

	$effect(() => {
		if (browser && !initialized) {
			initialized = true;
			loadCommands();
		}
	});

	async function loadCommands() {
		try {
			const data = await getCommonCommands();
			commands = data.commands;
		} catch (e) {
			console.error('Failed to load commands:', e);
		}
	}

	async function executeGmCommand() {
		if (!gmCommand.trim()) return;
		try {
			const result = await sendGmCommand(gmCommand);
			gmResult = JSON.stringify(result, null, 2);
		} catch (e) {
			gmResult = `Error: ${e instanceof Error ? e.message : 'Unknown error'}`;
		}
	}

	async function sendChat() {
		if (!chatMessage.trim() || chatLoading) return;

		const userMessage = chatMessage;
		chatMessage = '';
		chatHistory = [...chatHistory, { role: 'user', content: userMessage }];
		chatLoading = true;

		try {
			const result = await testChat(userMessage, chatHistory.slice(0, -1));
			chatHistory = [...chatHistory, { role: 'assistant', content: result.response }];
		} catch (e) {
			chatHistory = [
				...chatHistory,
				{ role: 'assistant', content: `Error: ${e instanceof Error ? e.message : 'Failed'}` }
			];
		} finally {
			chatLoading = false;
		}
	}

	function clearChat() {
		chatHistory = [];
	}

	function insertCommand(cmd: string) {
		gmCommand = cmd;
	}
</script>

<div class="console-page">
	<h1>Console</h1>

	<div class="grid">
		<!-- GM Commands -->
		<div class="card">
			<h2>GM Commands</h2>
			<div class="command-input">
				<input
					type="text"
					bind:value={gmCommand}
					placeholder=".server info"
					on:keydown={(e) => e.key === 'Enter' && executeGmCommand()}
				/>
				<button class="primary" on:click={executeGmCommand}>Execute</button>
			</div>
			{#if gmResult}
				<pre class="result">{gmResult}</pre>
			{/if}
			<div class="quick-commands">
				<h3>Quick Commands</h3>
				<div class="command-list">
					{#each commands as cmd}
						<button class="command-btn" on:click={() => insertCommand(cmd.cmd)} title={cmd.desc}>
							{cmd.cmd}
						</button>
					{/each}
				</div>
			</div>
		</div>

		<!-- LLM Chat Test -->
		<div class="card chat-card">
			<div class="chat-header">
				<h2>LLM Test Chat</h2>
				<button class="secondary" on:click={clearChat}>Clear</button>
			</div>
			<div class="chat-messages">
				{#if chatHistory.length === 0}
					<p class="empty">Test the LLM connection by sending a message.</p>
				{:else}
					{#each chatHistory as msg}
						<div class="message {msg.role}">
							<span class="role">{msg.role === 'user' ? 'You' : 'LLM'}</span>
							<p>{msg.content}</p>
						</div>
					{/each}
					{#if chatLoading}
						<div class="message assistant loading">
							<span class="role">LLM</span>
							<p>Thinking...</p>
						</div>
					{/if}
				{/if}
			</div>
			<div class="chat-input">
				<input
					type="text"
					bind:value={chatMessage}
					placeholder="Type a message..."
					on:keydown={(e) => e.key === 'Enter' && sendChat()}
					disabled={chatLoading}
				/>
				<button class="primary" on:click={sendChat} disabled={chatLoading}>Send</button>
			</div>
		</div>
	</div>
</div>

<style>
	.console-page {
		max-width: 1000px;
	}

	h1 {
		font-size: 2rem;
		font-weight: 600;
		margin-bottom: 2rem;
	}

	h2 {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 1rem;
		color: var(--text-muted);
		text-transform: uppercase;
	}

	h3 {
		font-size: 0.75rem;
		color: var(--text-muted);
		margin-bottom: 0.5rem;
		text-transform: uppercase;
	}

	.grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}

	.command-input {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	.command-input input {
		flex: 1;
	}

	.result {
		background: var(--bg-dark);
		padding: 1rem;
		border-radius: 8px;
		font-size: 0.75rem;
		overflow-x: auto;
		margin-bottom: 1rem;
	}

	.quick-commands {
		border-top: 1px solid var(--border);
		padding-top: 1rem;
	}

	.command-list {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.command-btn {
		font-family: monospace;
		font-size: 0.75rem;
		padding: 0.25rem 0.5rem;
		background: var(--bg-dark);
		color: var(--accent);
		border-radius: 4px;
	}

	.command-btn:hover {
		background: var(--bg-card-hover);
	}

	/* Chat */
	.chat-card {
		display: flex;
		flex-direction: column;
		max-height: 500px;
	}

	.chat-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.chat-header h2 {
		margin: 0;
	}

	.chat-messages {
		flex: 1;
		overflow-y: auto;
		padding: 1rem 0;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.empty {
		color: var(--text-muted);
		text-align: center;
		padding: 2rem;
	}

	.message {
		padding: 0.75rem;
		border-radius: 8px;
	}

	.message.user {
		background: var(--accent);
		color: white;
		margin-left: 2rem;
	}

	.message.assistant {
		background: var(--bg-dark);
		margin-right: 2rem;
	}

	.message.loading {
		opacity: 0.7;
	}

	.role {
		font-size: 0.675rem;
		text-transform: uppercase;
		opacity: 0.7;
		display: block;
		margin-bottom: 0.25rem;
	}

	.message p {
		margin: 0;
		line-height: 1.5;
	}

	.chat-input {
		display: flex;
		gap: 0.5rem;
		padding-top: 1rem;
		border-top: 1px solid var(--border);
	}

	.chat-input input {
		flex: 1;
	}
</style>
