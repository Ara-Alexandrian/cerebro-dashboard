/**
 * Cerebro Dashboard API Client
 */

const BASE_URL = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
	const response = await fetch(`${BASE_URL}${path}`, {
		headers: {
			'Content-Type': 'application/json',
			...options?.headers
		},
		...options
	});

	if (!response.ok) {
		throw new Error(`API error: ${response.status}`);
	}

	return response.json();
}

// Health & Monitoring
export async function getHealth() {
	return request<{
		azerothcore: { worldserver: string; authserver: string };
		vllm: { status: string };
		redis: { status: string };
		postgresql: { status: string };
		overall: string;
	}>('/monitor/health');
}

export async function getStats() {
	return request<{ active_bots: number; stats: Record<string, string> }>('/monitor/stats');
}

export async function getVllmStatus() {
	return request<{ health: { status: string }; models: Array<{ id: string }> }>('/monitor/vllm');
}

// Server
export async function getServerStatus() {
	return request<{ worldserver: string; authserver: string }>('/server/status');
}

export async function getConfigs() {
	return request<{ configs: Array<{ name: string; path: string; size: number }> }>('/server/configs');
}

export async function getConfig(filename: string) {
	return request<{ filename: string; content: string }>(`/server/configs/${filename}`);
}

// Bots / Personalities
export interface Personality {
	id: number;
	name: string;
	class: string;
	archetype: string;
	traits: Record<string, unknown>;
	system_prompt?: string;
	created_at: string;
	updated_at: string;
}

export async function getPersonalities() {
	return request<{ personalities: Personality[] }>('/bots/');
}

export async function getPersonality(id: number) {
	return request<Personality>(`/bots/${id}`);
}

export async function createPersonality(data: {
	name: string;
	class_: string;
	archetype: string;
	traits?: Record<string, unknown>;
	system_prompt?: string;
}) {
	return request<Personality>('/bots/', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export async function updatePersonality(id: number, data: Partial<{
	name: string;
	class_: string;
	archetype: string;
	traits: Record<string, unknown>;
	system_prompt: string;
}>) {
	return request<Personality>(`/bots/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

export async function deletePersonality(id: number) {
	return request<{ deleted: boolean }>(`/bots/${id}`, { method: 'DELETE' });
}

// Memories
export interface Memory {
	id: number;
	bot_id: number;
	bot_name: string;
	session_id: string;
	content: string;
	memory_type: string;
	importance: number;
	created_at: string;
}

export async function getMemories(params?: { bot_id?: number; memory_type?: string; limit?: number }) {
	const query = new URLSearchParams();
	if (params?.bot_id) query.set('bot_id', params.bot_id.toString());
	if (params?.memory_type) query.set('memory_type', params.memory_type);
	if (params?.limit) query.set('limit', params.limit.toString());

	return request<{ memories: Memory[] }>(`/memories/?${query}`);
}

export async function searchMemories(query: string, bot_id?: number) {
	const params = new URLSearchParams({ query });
	if (bot_id) params.set('bot_id', bot_id.toString());

	return request<{ memories: Memory[]; query: string }>(`/memories/search?${params}`);
}

// Console
export async function sendGmCommand(command: string) {
	return request<{ command: string; note: string }>('/console/gm', {
		method: 'POST',
		body: JSON.stringify({ command })
	});
}

export async function testChat(message: string, context: Array<{ role: string; content: string }> = []) {
	return request<{ response: string; model: string }>('/console/chat', {
		method: 'POST',
		body: JSON.stringify({ message, context })
	});
}

export async function getCommonCommands() {
	return request<{ commands: Array<{ cmd: string; desc: string }> }>('/console/commands');
}

// Accounts
export interface Account {
	id: number;
	username: string;
	email: string;
	last_login: string | null;
	online: number;
	totaltime: number;
	joindate: string;
	last_ip: string;
	expansion: number;
	locked: number;
}

export interface Character {
	guid: number;
	name: string;
	race: number;
	class: number;
	level: number;
	zone: number;
	map: number;
	online: number;
	totaltime: number;
	totalKills: number;
	todayKills: number;
}

export interface OnlineAccount extends Account {
	character_name: string | null;
	level: number | null;
	race: number | null;
	class: number | null;
	zone: number | null;
}

export async function getAccounts(includeBots: boolean = false, category?: string) {
	const params = new URLSearchParams({ include_bots: String(includeBots) });
	if (category) params.set('category', category);
	return request<{ accounts: AccountWithMeta[] }>(`/accounts?${params}`);
}

export interface AccountWithMeta extends Account {
	category: string;
	tags: string[];
	notes: string;
}

export async function searchAccounts(query: string, category?: string, includeBots: boolean = false) {
	const params = new URLSearchParams({
		q: query,
		include_bots: String(includeBots)
	});
	if (category) params.set('category', category);
	return request<{ accounts: AccountWithMeta[]; query: string }>(`/accounts/search?${params}`);
}

export async function getCategories() {
	return request<{ categories: string[] }>('/accounts/categories');
}

export async function setAccountMeta(accountId: number, data: {
	category?: string;
	tags?: string[];
	notes?: string;
}) {
	return request<AccountWithMeta>(`/accounts/${accountId}/meta`, {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

export async function getAccountStats() {
	return request<{ total: number; online: number; bots: number; players: number }>('/accounts/stats');
}

export async function getOnlineAccounts() {
	return request<{ online: OnlineAccount[] }>('/accounts/online');
}

export async function getAccount(id: number) {
	return request<Account>(`/accounts/${id}`);
}

export async function getAccountCharacters(id: number) {
	return request<{ characters: Character[] }>(`/accounts/${id}/characters`);
}

export async function createAccount(username: string, password: string, email?: string) {
	return request<{ success: boolean; id?: number; username?: string; error?: string }>('/accounts', {
		method: 'POST',
		body: JSON.stringify({ username, password, email: email || '' })
	});
}

export async function getGmLevel(accountId: number) {
	return request<{ gm_level: number }>(`/accounts/${accountId}/gmlevel`);
}

export async function setGmLevel(accountId: number, gmLevel: number, realmId: number = -1) {
	return request<{ success: boolean }>(`/accounts/${accountId}/gmlevel`, {
		method: 'POST',
		body: JSON.stringify({ gm_level: gmLevel, realm_id: realmId })
	});
}

export async function changePassword(accountId: number, password: string) {
	return request<{ success: boolean }>(`/accounts/${accountId}/password`, {
		method: 'POST',
		body: JSON.stringify({ password })
	});
}
