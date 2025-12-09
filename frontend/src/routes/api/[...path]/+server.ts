import type { RequestHandler } from './$types';

const BACKEND_URL = process.env.BACKEND_URL || 'http://cerebro-backend:8080';

export const GET: RequestHandler = async ({ params, url }) => {
	return proxyRequest('GET', params.path, url.search);
};

export const POST: RequestHandler = async ({ params, url, request }) => {
	const body = await request.text();
	return proxyRequest('POST', params.path, url.search, body);
};

export const PUT: RequestHandler = async ({ params, url, request }) => {
	const body = await request.text();
	return proxyRequest('PUT', params.path, url.search, body);
};

export const DELETE: RequestHandler = async ({ params, url }) => {
	return proxyRequest('DELETE', params.path, url.search);
};

async function proxyRequest(
	method: string,
	path: string,
	search: string,
	body?: string
): Promise<Response> {
	const backendUrl = `${BACKEND_URL}/api/${path}${search}`;

	try {
		const response = await fetch(backendUrl, {
			method,
			headers: {
				'Content-Type': 'application/json',
				'Accept': 'application/json'
			},
			body: body || undefined
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
