<script lang="ts">
	import { browser } from '$app/environment';
	import {
		getAccounts,
		searchAccounts,
		getAccountStats,
		getOnlineAccounts,
		getAccountCharacters,
		getCategories,
		createAccount,
		setAccountMeta,
		getGmLevel,
		setGmLevel,
		changePassword,
		type Account,
		type AccountWithMeta,
		type OnlineAccount,
		type Character
	} from '$lib/api';

	let accounts: AccountWithMeta[] = $state([]);
	let onlineAccounts: OnlineAccount[] = $state([]);
	let stats = $state({ total: 0, online: 0, bots: 0, players: 0 });
	let categories: string[] = $state(['friend', 'bot', 'admin', 'test', 'unknown']);
	let loading = $state(true);

	// Filters
	let searchQuery = $state('');
	let filterCategory = $state('');
	let showBots = $state(false);
	let showCreateForm = $state(false);

	// Selection
	let selectedAccount: AccountWithMeta | null = $state(null);
	let selectedCharacters: Character[] = $state([]);

	// Create form
	let newUsername = $state('');
	let newPassword = $state('');
	let newEmail = $state('');
	let createError = $state('');

	// Edit meta
	let editingMeta = $state(false);
	let editCategory = $state('');
	let editNotes = $state('');
	let editTags = $state('');

	// GM Level and Password
	let currentGmLevel = $state(0);
	let showGmInfo = $state(false);
	let changePasswordValue = $state('');
	let passwordError = $state('');
	let passwordSuccess = $state(false);

	const CLASS_NAMES: Record<number, string> = {
		1: 'Warrior', 2: 'Paladin', 3: 'Hunter', 4: 'Rogue',
		5: 'Priest', 6: 'Death Knight', 7: 'Shaman', 8: 'Mage',
		9: 'Warlock', 11: 'Druid'
	};

	const RACE_NAMES: Record<number, string> = {
		1: 'Human', 2: 'Orc', 3: 'Dwarf', 4: 'Night Elf',
		5: 'Undead', 6: 'Tauren', 7: 'Gnome', 8: 'Troll',
		10: 'Blood Elf', 11: 'Draenei'
	};

	const CATEGORY_COLORS: Record<string, string> = {
		friend: '#22c55e',
		admin: '#f59e0b',
		bot: '#6b7280',
		test: '#8b5cf6',
		unknown: '#64748b'
	};

	let searchTimeout: ReturnType<typeof setTimeout>;

	async function refresh() {
		try {
			const [statsData, onlineData, catData] = await Promise.all([
				getAccountStats(),
				getOnlineAccounts(),
				getCategories()
			]);
			stats = statsData;
			onlineAccounts = onlineData.online;
			categories = catData.categories;

			await loadAccounts();
		} catch (e) {
			console.error('Failed to load:', e);
		} finally {
			loading = false;
		}
	}

	async function loadAccounts() {
		if (searchQuery.trim()) {
			const data = await searchAccounts(searchQuery, filterCategory || undefined, showBots);
			accounts = data.accounts;
		} else {
			const data = await getAccounts(showBots, filterCategory || undefined);
			accounts = data.accounts;
		}
	}

	function handleSearch() {
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(loadAccounts, 300);
	}

	$effect(() => {
		if (!browser) return;
		refresh();
		const interval = setInterval(() => {
			getOnlineAccounts().then(d => onlineAccounts = d.online);
			getAccountStats().then(d => stats = d);
		}, 10000);
		return () => clearInterval(interval);
	});

	async function handleFilterChange() {
		loading = true;
		await loadAccounts();
		loading = false;
	}

	async function selectAccount(account: AccountWithMeta) {
		selectedAccount = account;
		editingMeta = false;
		changePasswordValue = '';
		passwordError = '';
		passwordSuccess = false;
		try {
			const [charData, gmData] = await Promise.all([
				getAccountCharacters(account.id),
				getGmLevel(account.id)
			]);
			selectedCharacters = charData.characters;
			currentGmLevel = gmData.gm_level;
		} catch (e) {
			console.error('Failed to load account details:', e);
			selectedCharacters = [];
			currentGmLevel = 0;
		}
	}

	function startEditMeta() {
		if (!selectedAccount) return;
		editCategory = selectedAccount.category;
		editNotes = selectedAccount.notes || '';
		editTags = (selectedAccount.tags || []).join(', ');
		editingMeta = true;
	}

	async function saveMeta() {
		if (!selectedAccount) return;
		try {
			const tags = editTags.split(',').map(t => t.trim()).filter(Boolean);
			const updated = await setAccountMeta(selectedAccount.id, {
				category: editCategory,
				notes: editNotes,
				tags
			});
			selectedAccount = { ...selectedAccount, ...updated };
			// Update in list
			accounts = accounts.map(a =>
				a.id === selectedAccount!.id ? { ...a, ...updated } : a
			);
			editingMeta = false;
		} catch (e) {
			console.error('Failed to save:', e);
		}
	}

	async function quickSetCategory(account: AccountWithMeta, category: string) {
		try {
			const updated = await setAccountMeta(account.id, { category });
			accounts = accounts.map(a =>
				a.id === account.id ? { ...a, category: updated.category } : a
			);
			if (selectedAccount?.id === account.id) {
				selectedAccount = { ...selectedAccount, category: updated.category };
			}
		} catch (e) {
			console.error('Failed to set category:', e);
		}
	}

	async function handleSetGmLevel(level: number) {
		if (!selectedAccount) return;
		try {
			await setGmLevel(selectedAccount.id, level);
			currentGmLevel = level;
		} catch (e) {
			console.error('Failed to set GM level:', e);
		}
	}

	async function handleChangePassword() {
		if (!selectedAccount) return;
		passwordError = '';
		passwordSuccess = false;

		if (changePasswordValue.length < 4) {
			passwordError = 'Password must be at least 4 characters';
			return;
		}

		try {
			await changePassword(selectedAccount.id, changePasswordValue);
			passwordSuccess = true;
			changePasswordValue = '';
			setTimeout(() => passwordSuccess = false, 3000);
		} catch (e) {
			passwordError = e instanceof Error ? e.message : 'Failed to change password';
		}
	}

	async function handleCreate() {
		createError = '';
		if (!newUsername || !newPassword) {
			createError = 'Username and password required';
			return;
		}
		try {
			const result = await createAccount(newUsername, newPassword, newEmail);
			if (result.success) {
				showCreateForm = false;
				newUsername = '';
				newPassword = '';
				newEmail = '';
				await loadAccounts();
			} else {
				createError = result.error || 'Failed';
			}
		} catch (e) {
			createError = e instanceof Error ? e.message : 'Failed';
		}
	}

	function formatPlaytime(seconds: number): string {
		const hours = Math.floor(seconds / 3600);
		const minutes = Math.floor((seconds % 3600) / 60);
		if (hours > 0) return `${hours}h ${minutes}m`;
		return `${minutes}m`;
	}

	function isBot(username: string): boolean {
		return username.startsWith('RNDBOT');
	}
</script>

<div class="accounts-page">
	<header>
		<h1>Accounts</h1>
		<button class="secondary" onclick={() => showCreateForm = !showCreateForm}>
			{showCreateForm ? 'Cancel' : '+ New Account'}
		</button>
	</header>

	<!-- Stats Bar -->
	<div class="stats-bar">
		<div class="stat">
			<span class="stat-value">{stats.players}</span>
			<span class="stat-label">Players</span>
		</div>
		<div class="stat">
			<span class="stat-value online">{stats.online}</span>
			<span class="stat-label">Online</span>
		</div>
		<div class="stat">
			<span class="stat-value">{stats.bots}</span>
			<span class="stat-label">Bots</span>
		</div>
	</div>

	<!-- Create Form -->
	{#if showCreateForm}
		<div class="card create-form">
			<h2>Create Account</h2>
			<div class="form-row">
				<label>
					<span>Username</span>
					<input type="text" bind:value={newUsername} placeholder="Username" />
				</label>
				<label>
					<span>Password</span>
					<input type="password" bind:value={newPassword} placeholder="Password" />
				</label>
				<label>
					<span>Email (optional)</span>
					<input type="email" bind:value={newEmail} placeholder="email@example.com" />
				</label>
			</div>
			{#if createError}
				<div class="error">{createError}</div>
			{/if}
			<div class="form-actions">
				<button class="primary" onclick={handleCreate}>Create Account</button>
			</div>
		</div>
	{/if}

	<!-- Search & Filters -->
	<div class="filters card">
		<div class="filter-row">
			<input
				type="text"
				placeholder="Search accounts..."
				bind:value={searchQuery}
				oninput={handleSearch}
			/>
			<select bind:value={filterCategory} onchange={handleFilterChange}>
				<option value="">All Categories</option>
				{#each categories as cat}
					<option value={cat}>{cat}</option>
				{/each}
			</select>
			<label class="toggle">
				<input type="checkbox" bind:checked={showBots} onchange={handleFilterChange} />
				<span>Bots</span>
			</label>
		</div>
	</div>

	<!-- Online Now -->
	{#if onlineAccounts.filter(a => !isBot(a.username)).length > 0}
		<div class="card online-section">
			<h2>Players Online ({onlineAccounts.filter(a => !isBot(a.username)).length})</h2>
			<div class="online-list">
				{#each onlineAccounts.filter(a => !isBot(a.username)) as acc}
					<div class="online-item">
						<span class="online-dot"></span>
						<span class="online-name">{acc.username}</span>
						{#if acc.character_name}
							<span class="online-char">
								{acc.character_name} (Lv.{acc.level} {RACE_NAMES[acc.race ?? 0]} {CLASS_NAMES[acc.class ?? 0]})
							</span>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<div class="content-layout">
		<!-- Account List -->
		<div class="account-list">
			<div class="list-header">
				<h2>Accounts ({accounts.length})</h2>
			</div>

			{#if loading}
				<div class="loading">Loading...</div>
			{:else if accounts.length === 0}
				<div class="empty">No accounts found</div>
			{:else}
				<div class="accounts-table">
					<div class="table-header">
						<span>Username</span>
						<span>Category</span>
						<span>Status</span>
						<span>Playtime</span>
					</div>
					{#each accounts as account}
						<button
							class="table-row"
							class:selected={selectedAccount?.id === account.id}
							class:online={account.online === 1}
							onclick={() => selectAccount(account)}
						>
							<span class="username">{account.username}</span>
							<span class="category">
								<span
									class="category-badge"
									style="background: {CATEGORY_COLORS[account.category]}20; color: {CATEGORY_COLORS[account.category]}"
								>
									{account.category}
								</span>
							</span>
							<span class="status">
								{#if account.online === 1}
									<span class="status-badge online">Online</span>
								{:else}
									<span class="status-badge offline">Offline</span>
								{/if}
							</span>
							<span class="playtime">{formatPlaytime(account.totaltime)}</span>
						</button>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Account Detail -->
		{#if selectedAccount}
			<div class="card account-detail">
				<div class="detail-header">
					<h2>{selectedAccount.username}</h2>
					<span
						class="category-badge large"
						style="background: {CATEGORY_COLORS[selectedAccount.category]}20; color: {CATEGORY_COLORS[selectedAccount.category]}"
					>
						{selectedAccount.category}
					</span>
				</div>

				{#if editingMeta}
					<div class="edit-meta">
						<label>
							<span>Category</span>
							<select bind:value={editCategory}>
								{#each categories as cat}
									<option value={cat}>{cat}</option>
								{/each}
							</select>
						</label>
						<label>
							<span>Tags (comma separated)</span>
							<input type="text" bind:value={editTags} placeholder="tag1, tag2" />
						</label>
						<label>
							<span>Notes</span>
							<textarea bind:value={editNotes} rows="2"></textarea>
						</label>
						<div class="edit-actions">
							<button class="secondary" onclick={() => editingMeta = false}>Cancel</button>
							<button class="primary" onclick={saveMeta}>Save</button>
						</div>
					</div>
				{:else}
					<div class="quick-category">
						{#each categories.filter(c => c !== 'bot') as cat}
							<button
								class="cat-btn"
								class:active={selectedAccount.category === cat}
								style="--cat-color: {CATEGORY_COLORS[cat]}"
								onclick={() => selectedAccount && quickSetCategory(selectedAccount, cat)}
							>
								{cat}
							</button>
						{/each}
						<button class="edit-btn" onclick={startEditMeta}>Edit</button>
					</div>

					{#if selectedAccount.tags?.length}
						<div class="tags">
							{#each selectedAccount.tags as tag}
								<span class="tag">{tag}</span>
							{/each}
						</div>
					{/if}

					{#if selectedAccount.notes}
						<p class="notes">{selectedAccount.notes}</p>
					{/if}
				{/if}

				<div class="detail-grid">
					<div class="detail-item">
						<span class="label">Account ID</span>
						<span class="value">{selectedAccount.id}</span>
					</div>
					<div class="detail-item">
						<span class="label">Status</span>
						<span class="value">{selectedAccount.online === 1 ? 'Online' : 'Offline'}</span>
					</div>
					<div class="detail-item">
						<span class="label">Playtime</span>
						<span class="value">{formatPlaytime(selectedAccount.totaltime)}</span>
					</div>
					<div class="detail-item">
						<span class="label">Last Login</span>
						<span class="value">
							{selectedAccount.last_login ? new Date(selectedAccount.last_login).toLocaleString() : 'Never'}
						</span>
					</div>
					<div class="detail-item">
						<span class="label">Last IP</span>
						<span class="value">{selectedAccount.last_ip}</span>
					</div>
					<div class="detail-item">
						<span class="label">Joined</span>
						<span class="value">{new Date(selectedAccount.joindate).toLocaleDateString()}</span>
					</div>
				</div>

				<!-- GM Level -->
				<div class="admin-section">
					<h3>
						GM Level
						<button class="info-btn" onclick={() => showGmInfo = !showGmInfo} title="What do GM levels do?">?</button>
					</h3>
					{#if showGmInfo}
						<div class="info-box">
							<div class="info-item"><strong>0 - Player:</strong> Normal player, no GM commands</div>
							<div class="info-item"><strong>1 - Moderator:</strong> Basic commands (teleport, summon, kick, mute)</div>
							<div class="info-item"><strong>2 - Game Master:</strong> Extended commands (spawn items/NPCs, modify characters)</div>
							<div class="info-item"><strong>3 - Admin:</strong> Full access (server commands, account management, .reload)</div>
						</div>
					{/if}
					<div class="gm-buttons">
						{#each [0, 1, 2, 3] as level}
							<button
								class="gm-btn"
								class:active={currentGmLevel === level}
								onclick={() => handleSetGmLevel(level)}
							>
								{level === 0 ? 'Player' : `GM ${level}`}
							</button>
						{/each}
					</div>
				</div>

				<!-- Change Password -->
				<div class="admin-section">
					<h3>Change Password</h3>
					<div class="password-form">
						<input
							type="password"
							placeholder="New password..."
							bind:value={changePasswordValue}
						/>
						<button class="primary" onclick={handleChangePassword}>Set</button>
					</div>
					{#if passwordError}
						<div class="error-msg">{passwordError}</div>
					{/if}
					{#if passwordSuccess}
						<div class="success-msg">Password changed!</div>
					{/if}
				</div>

				{#if selectedCharacters.length > 0}
					<h3>Characters ({selectedCharacters.length})</h3>
					<div class="character-list">
						{#each selectedCharacters as char}
							<div class="character-item" class:online={char.online === 1}>
								<span class="char-name">{char.name}</span>
								<span class="char-info">
									Lv.{char.level} {RACE_NAMES[char.race]} {CLASS_NAMES[char.class]}
								</span>
								<span class="char-time">{formatPlaytime(char.totaltime)}</span>
							</div>
						{/each}
					</div>
				{:else}
					<p class="no-chars">No characters</p>
				{/if}
			</div>
		{/if}
	</div>
</div>

<style>
	.accounts-page {
		max-width: 1200px;
	}

	header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	h1 { font-size: 2rem; font-weight: 600; }
	h2 { font-size: 1rem; font-weight: 600; margin-bottom: 1rem; color: var(--text-muted); text-transform: uppercase; }
	h3 { font-size: 0.875rem; font-weight: 600; margin: 1.5rem 0 0.75rem; color: var(--text-muted); text-transform: uppercase; }

	.stats-bar {
		display: flex;
		gap: 1.5rem;
		margin-bottom: 1.5rem;
		padding: 1rem 1.5rem;
		background: var(--bg-card);
		border-radius: 8px;
		border: 1px solid var(--border);
	}

	.stat { display: flex; flex-direction: column; align-items: center; gap: 0.25rem; }
	.stat-value { font-size: 1.5rem; font-weight: 700; color: var(--accent); }
	.stat-value.online { color: var(--success); }
	.stat-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; }

	.filters { margin-bottom: 1.5rem; }
	.filter-row { display: flex; gap: 1rem; align-items: center; }
	.filter-row input[type="text"] { flex: 1; }
	.filter-row select { min-width: 140px; }

	.toggle { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; font-size: 0.875rem; white-space: nowrap; }

	.create-form { margin-bottom: 1.5rem; }
	.form-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1rem; }
	.form-row label { display: flex; flex-direction: column; gap: 0.5rem; }
	.form-row label span { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; }
	.error { color: var(--error); margin-bottom: 1rem; }
	.form-actions { display: flex; justify-content: flex-end; }

	.online-section { margin-bottom: 1.5rem; }
	.online-list { display: flex; flex-wrap: wrap; gap: 0.75rem; }
	.online-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; background: var(--bg-dark); border-radius: 6px; font-size: 0.875rem; }
	.online-dot { width: 8px; height: 8px; background: var(--success); border-radius: 50%; }
	.online-name { font-weight: 600; }
	.online-char { color: var(--text-muted); font-size: 0.75rem; }

	.content-layout { display: grid; grid-template-columns: 1fr 380px; gap: 1.5rem; }
	.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
	.list-header h2 { margin: 0; }

	.loading, .empty { text-align: center; padding: 2rem; color: var(--text-muted); }

	.accounts-table { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; max-height: 600px; overflow-y: auto; }
	.table-header { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; padding: 0.75rem 1rem; background: var(--bg-dark); font-size: 0.75rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; position: sticky; top: 0; }
	.table-row { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; padding: 0.75rem 1rem; border-top: 1px solid var(--border); background: transparent; width: 100%; text-align: left; cursor: pointer; transition: background 0.15s; }
	.table-row:hover { background: var(--bg-card-hover); }
	.table-row.selected { background: var(--accent); color: white; }
	.table-row.online .username { color: var(--success); }
	.table-row.selected .username { color: white; }

	.username { font-weight: 500; }
	.category-badge { font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 4px; text-transform: capitalize; }
	.category-badge.large { font-size: 0.8rem; padding: 0.25rem 0.75rem; }
	.table-row.selected .category-badge { background: rgba(255,255,255,0.2) !important; color: white !important; }

	.status-badge { font-size: 0.75rem; padding: 0.125rem 0.5rem; border-radius: 4px; }
	.status-badge.online { background: rgba(34, 197, 94, 0.2); color: var(--success); }
	.status-badge.offline { background: var(--bg-dark); color: var(--text-muted); }
	.table-row.selected .status-badge { background: rgba(255,255,255,0.2); color: white; }

	.playtime { font-size: 0.875rem; color: var(--text-muted); }
	.table-row.selected .playtime { color: rgba(255,255,255,0.8); }

	.account-detail { position: sticky; top: 1rem; }
	.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
	.detail-header h2 { margin: 0; }

	.quick-category { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
	.cat-btn { font-size: 0.75rem; padding: 0.25rem 0.75rem; border-radius: 4px; background: var(--bg-dark); color: var(--text-muted); transition: all 0.15s; }
	.cat-btn:hover { background: color-mix(in srgb, var(--cat-color) 20%, transparent); color: var(--cat-color); }
	.cat-btn.active { background: color-mix(in srgb, var(--cat-color) 20%, transparent); color: var(--cat-color); font-weight: 600; }
	.edit-btn { font-size: 0.75rem; padding: 0.25rem 0.75rem; border-radius: 4px; background: var(--bg-dark); color: var(--text-muted); margin-left: auto; }
	.edit-btn:hover { color: var(--accent); }

	.tags { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
	.tag { font-size: 0.7rem; padding: 0.15rem 0.5rem; background: var(--bg-dark); border-radius: 4px; color: var(--text-muted); }
	.notes { font-size: 0.875rem; color: var(--text-muted); margin-bottom: 1rem; font-style: italic; }

	.edit-meta { display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1rem; padding: 1rem; background: var(--bg-dark); border-radius: 8px; }
	.edit-meta label { display: flex; flex-direction: column; gap: 0.25rem; }
	.edit-meta label span { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; }
	.edit-meta textarea { resize: vertical; min-height: 60px; }
	.edit-actions { display: flex; gap: 0.5rem; justify-content: flex-end; }

	.detail-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; }
	.detail-item { display: flex; flex-direction: column; gap: 0.25rem; }
	.detail-item .label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; }
	.detail-item .value { font-size: 0.875rem; }

	.character-list { display: flex; flex-direction: column; gap: 0.5rem; }
	.character-item { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0.75rem; background: var(--bg-dark); border-radius: 6px; }
	.character-item.online { border-left: 3px solid var(--success); }
	.char-name { font-weight: 600; }
	.char-info, .char-time { font-size: 0.75rem; color: var(--text-muted); }
	.no-chars { color: var(--text-muted); font-style: italic; }

	.admin-section { margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border); }
	.admin-section h3 { margin-top: 0; display: flex; align-items: center; gap: 0.5rem; }

	.info-btn { width: 18px; height: 18px; border-radius: 50%; background: var(--bg-dark); color: var(--text-muted); font-size: 0.7rem; font-weight: 600; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.15s; }
	.info-btn:hover { background: var(--accent); color: white; }

	.info-box { background: var(--bg-dark); border-radius: 6px; padding: 0.75rem; margin-bottom: 0.75rem; font-size: 0.75rem; }
	.info-item { padding: 0.25rem 0; color: var(--text-muted); }
	.info-item strong { color: var(--text); }

	.gm-buttons { display: flex; gap: 0.5rem; }
	.gm-btn { font-size: 0.75rem; padding: 0.375rem 0.75rem; border-radius: 4px; background: var(--bg-dark); color: var(--text-muted); transition: all 0.15s; flex: 1; }
	.gm-btn:hover { background: var(--accent); color: white; }
	.gm-btn.active { background: var(--accent); color: white; font-weight: 600; }

	.password-form { display: flex; gap: 0.5rem; }
	.password-form input { flex: 1; }
	.password-form button { white-space: nowrap; }

	.error-msg { color: var(--error); font-size: 0.75rem; margin-top: 0.5rem; }
	.success-msg { color: var(--success); font-size: 0.75rem; margin-top: 0.5rem; }
</style>
