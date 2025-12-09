# Svelte 5 Migration Notes

This document captures critical lessons learned from migrating/fixing the Cerebro Dashboard to work properly with Svelte 5.

## Key Issue: `onMount` Doesn't Fire with `ssr=false`

### The Problem
When using `export const ssr = false` in `+page.ts` files (which disables server-side rendering), Svelte 5's `onMount` lifecycle function does **not** fire reliably. This caused pages to get stuck on "Loading..." state indefinitely.

The error manifested as:
```
Uncaught (in promise) TypeError: Cannot read properties of null (reading 'r')
```

This cryptic error came from Svelte 5's internal signal system when `onMount` callbacks weren't executing properly.

### The Solution: Use Svelte 5 Runes

Replace the traditional Svelte pattern with Svelte 5 runes:

#### Before (Broken)
```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';

  let data = null;
  let loading = true;

  onMount(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  });
</script>
```

#### After (Working)
```svelte
<script lang="ts">
  import { browser } from '$app/environment';

  let data = $state(null);
  let loading = $state(true);
  let initialized = $state(false);
  let interval = $state(null);

  $effect(() => {
    if (browser && !initialized) {
      initialized = true;
      fetchData();
      interval = setInterval(fetchData, 5000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  });
</script>
```

### Key Points

1. **Use `$state()` instead of `let`** for reactive variables
2. **Use `$effect()` instead of `onMount()`** for side effects and lifecycle
3. **Check `browser` inside `$effect()`** since effects can run during SSR
4. **Use an `initialized` flag** to prevent the effect from running multiple times
5. **Return cleanup function from `$effect()`** just like you would from `onMount`

## API Proxy for Production

### The Problem
Vite's `proxy` configuration in `vite.config.ts` only works in development mode. In production builds, client-side fetch calls to `/api/*` endpoints fail because there's no proxy.

### The Solution
Create a SvelteKit server route to proxy API requests:

**File: `src/routes/api/[...path]/+server.ts`**
```typescript
import type { RequestHandler } from './$types';

const BACKEND_URL = process.env.BACKEND_URL || 'http://cerebro-backend:8080';

export const GET: RequestHandler = async ({ params, url }) => {
  return proxyRequest('GET', params.path, url.search);
};

export const POST: RequestHandler = async ({ params, url, request }) => {
  const body = await request.text();
  return proxyRequest('POST', params.path, url.search, body);
};

// ... PUT, DELETE handlers

async function proxyRequest(method: string, path: string, search: string, body?: string) {
  const backendUrl = `${BACKEND_URL}/api/${path}${search}`;
  // ... fetch and return
}
```

## Docker Networking

### The Problem
Hardcoded IP addresses in `docker-compose.yml` can become stale when containers restart and get different IPs.

### The Solution
Use Docker DNS names (container names) instead of IPs:

```yaml
# Bad
- POSTGRES_HOST=172.21.0.2

# Good
- POSTGRES_HOST=azerothcore-pgvector
```

This works because all containers are on the same Docker network (`azerothcore`) which provides automatic DNS resolution.

## Files Modified

All route pages were converted to Svelte 5 runes:
- `src/routes/+page.svelte` (Dashboard)
- `src/routes/accounts/+page.svelte`
- `src/routes/bots/+page.svelte`
- `src/routes/config/+page.svelte`
- `src/routes/console/+page.svelte`
- `src/routes/memories/+page.svelte`
- `src/routes/monitor/+page.svelte`
- `src/routes/server/+page.svelte`

## Testing Changes

After making changes, rebuild and restart:
```bash
cd /mnt/nextorage/appdata/wotlk/cerebro-dashboard
./deploy.sh restart
```

Check container logs:
```bash
docker logs cerebro-backend -f
docker logs cerebro-frontend -f
```
