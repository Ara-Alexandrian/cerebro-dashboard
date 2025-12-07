import type { Handle } from '@sveltejs/kit';

const BACKEND_URL = process.env.BACKEND_URL || 'http://cerebro-backend:8080';

export const handle: Handle = async ({ event, resolve }) => {
	// Proxy /api/* requests to the backend
	if (event.url.pathname.startsWith('/api')) {
		const backendUrl = `${BACKEND_URL}${event.url.pathname}${event.url.search}`;

		try {
			const headers: Record<string, string> = {
				'Content-Type': 'application/json',
				'Accept': 'application/json'
			};

			const response = await fetch(backendUrl, {
				method: event.request.method,
				headers,
				body: event.request.method !== 'GET' && event.request.method !== 'HEAD'
					? await event.request.text()
					: undefined
			});

			const data = await response.text();

			return new Response(data, {
				status: response.status,
				headers: {
					'Content-Type': 'application/json'
				}
			});
		} catch (err) {
			console.error('API proxy error:', err);
			return new Response(JSON.stringify({ error: 'Backend unavailable' }), {
				status: 502,
				headers: { 'Content-Type': 'application/json' }
			});
		}
	}

	return resolve(event);
};
