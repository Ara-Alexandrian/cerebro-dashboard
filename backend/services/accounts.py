"""
Account management service - interfaces with AzerothCore MySQL
"""
import os
import hashlib
import asyncio
from typing import Optional
import aiomysql
from services.postgres_client import get_pool as get_pg_pool

# AzerothCore MySQL connection
AC_MYSQL_HOST = os.getenv("AC_MYSQL_HOST", "172.21.0.10")
AC_MYSQL_PORT = int(os.getenv("AC_MYSQL_PORT", "3306"))
AC_MYSQL_USER = os.getenv("AC_MYSQL_USER", "acore")
AC_MYSQL_PASS = os.getenv("AC_MYSQL_PASSWORD", "acore")
AC_MYSQL_DB = os.getenv("AC_MYSQL_AUTH_DB", "acore_auth")

# Account categories
CATEGORIES = ['friend', 'bot', 'admin', 'test', 'unknown']

_pool: Optional[aiomysql.Pool] = None


async def get_pool() -> aiomysql.Pool:
    """Get or create MySQL connection pool"""
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            host=AC_MYSQL_HOST,
            port=AC_MYSQL_PORT,
            user=AC_MYSQL_USER,
            password=AC_MYSQL_PASS,
            db=AC_MYSQL_DB,
            autocommit=True,
            minsize=1,
            maxsize=5
        )
    return _pool


async def list_accounts(include_bots: bool = True) -> list[dict]:
    """List all accounts from AzerothCore"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            if include_bots:
                await cur.execute("""
                    SELECT id, username, email, last_login, online, totaltime,
                           joindate, last_ip, expansion, locked
                    FROM account
                    ORDER BY id
                """)
            else:
                await cur.execute("""
                    SELECT id, username, email, last_login, online, totaltime,
                           joindate, last_ip, expansion, locked
                    FROM account
                    WHERE username NOT LIKE 'RNDBOT%'
                    ORDER BY id
                """)
            rows = await cur.fetchall()
            return [dict(row) for row in rows]


async def get_account(account_id: int) -> Optional[dict]:
    """Get single account details"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT id, username, email, last_login, online, totaltime,
                       joindate, last_ip, expansion, locked, failed_logins
                FROM account WHERE id = %s
            """, (account_id,))
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_account_characters(account_id: int) -> list[dict]:
    """Get characters for an account"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Switch to characters DB
            await cur.execute("USE acore_characters")
            await cur.execute("""
                SELECT guid, name, race, class, level, zone, map, online,
                       totaltime, totalKills, todayKills
                FROM characters
                WHERE account = %s
                ORDER BY level DESC
            """, (account_id,))
            rows = await cur.fetchall()
            # Switch back
            await cur.execute(f"USE {AC_MYSQL_DB}")
            return [dict(row) for row in rows]


async def get_online_accounts() -> list[dict]:
    """Get currently online accounts with character info"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT a.id, a.username, a.last_login, a.totaltime,
                       c.name as character_name, c.level, c.race, c.class, c.zone
                FROM account a
                LEFT JOIN acore_characters.characters c ON c.account = a.id AND c.online = 1
                WHERE a.online = 1
                ORDER BY a.username
            """)
            rows = await cur.fetchall()
            return [dict(row) for row in rows]


async def create_account(username: str, password: str, email: str = "") -> dict:
    """
    Create a new account using AzerothCore's SRP6 auth
    Note: AzerothCore uses SRP6 with salt/verifier, not plain passwords
    """
    import secrets

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Check if username exists
            await cur.execute(
                "SELECT id FROM account WHERE username = %s",
                (username.upper(),)
            )
            if await cur.fetchone():
                return {"success": False, "error": "Username already exists"}

            # Generate salt (32 bytes)
            salt = secrets.token_bytes(32)

            # Calculate verifier using SRP6
            # AzerothCore formula: verifier = g^H(salt | H(username | ":" | password)) mod N
            # Simplified: we'll use the game's expected format
            username_upper = username.upper()
            password_upper = password.upper()

            # Calculate H(username:password)
            h1 = hashlib.sha1(f"{username_upper}:{password_upper}".encode()).digest()

            # Calculate H(salt | h1)
            h2 = hashlib.sha1(salt + h1).digest()

            # Convert to integer for modular exponentiation
            # SRP6 parameters for WoW
            g = 7
            N = int("894B645E89E1535BBDAD5B8B290650530801B18EBFBF5E8FAB3C82872A3E9BB7", 16)

            # x = H(salt | H(username:password)) as integer (little-endian)
            x = int.from_bytes(h2, 'little')

            # v = g^x mod N
            v = pow(g, x, N)

            # Convert verifier to bytes (32 bytes, little-endian)
            verifier = v.to_bytes(32, 'little')

            # Insert account
            await cur.execute("""
                INSERT INTO account (username, salt, verifier, email, expansion)
                VALUES (%s, %s, %s, %s, 2)
            """, (username_upper, salt, verifier, email))

            # Get the new account ID
            await cur.execute("SELECT LAST_INSERT_ID() as id")
            result = await cur.fetchone()

            return {
                "success": True,
                "id": result["id"],
                "username": username_upper
            }


async def set_account_gm_level(account_id: int, gm_level: int, realm_id: int = -1) -> bool:
    """Set GM level for an account"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Delete existing access
            await cur.execute(
                "DELETE FROM account_access WHERE id = %s AND RealmID = %s",
                (account_id, realm_id)
            )

            if gm_level > 0:
                await cur.execute("""
                    INSERT INTO account_access (id, gmlevel, RealmID)
                    VALUES (%s, %s, %s)
                """, (account_id, gm_level, realm_id))

            return True


async def get_account_gm_level(account_id: int) -> int:
    """Get GM level for an account"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT gmlevel FROM account_access
                WHERE id = %s AND (RealmID = -1 OR RealmID = 1)
                ORDER BY RealmID DESC LIMIT 1
            """, (account_id,))
            row = await cur.fetchone()
            return row['gmlevel'] if row else 0


async def change_password(account_id: int, new_password: str) -> dict:
    """Change password for an account using SRP6"""
    import secrets

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Get username
            await cur.execute("SELECT username FROM account WHERE id = %s", (account_id,))
            row = await cur.fetchone()
            if not row:
                return {"success": False, "error": "Account not found"}

            username_upper = row['username'].upper()
            password_upper = new_password.upper()

            # Generate new salt
            salt = secrets.token_bytes(32)

            # Calculate verifier using SRP6
            h1 = hashlib.sha1(f"{username_upper}:{password_upper}".encode()).digest()
            h2 = hashlib.sha1(salt + h1).digest()

            g = 7
            N = int("894B645E89E1535BBDAD5B8B290650530801B18EBFBF5E8FAB3C82872A3E9BB7", 16)
            x = int.from_bytes(h2, 'little')
            v = pow(g, x, N)
            verifier = v.to_bytes(32, 'little')

            # Update account
            await cur.execute("""
                UPDATE account SET salt = %s, verifier = %s WHERE id = %s
            """, (salt, verifier, account_id))

            return {"success": True}


async def get_account_stats() -> dict:
    """Get account statistics"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN online = 1 THEN 1 ELSE 0 END) as online,
                    SUM(CASE WHEN username LIKE 'RNDBOT%' THEN 1 ELSE 0 END) as bots,
                    SUM(CASE WHEN username NOT LIKE 'RNDBOT%' THEN 1 ELSE 0 END) as players
                FROM account
            """)
            row = await cur.fetchone()
            return dict(row)


# --- Account Metadata (PostgreSQL) ---

async def get_account_meta(account_id: int) -> Optional[dict]:
    """Get account metadata from PostgreSQL"""
    pg = await get_pg_pool()
    async with pg.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM account_meta WHERE account_id = $1",
            account_id
        )
        if row:
            return dict(row)
        return None


async def get_all_account_meta() -> dict[int, dict]:
    """Get all account metadata as a dict keyed by account_id"""
    pg = await get_pg_pool()
    async with pg.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM account_meta")
        return {row['account_id']: dict(row) for row in rows}


async def set_account_meta(account_id: int, username: str, category: str = None,
                           tags: list[str] = None, notes: str = None) -> dict:
    """Set or update account metadata"""
    pg = await get_pg_pool()
    async with pg.acquire() as conn:
        # Check if exists
        existing = await conn.fetchrow(
            "SELECT * FROM account_meta WHERE account_id = $1", account_id
        )

        if existing:
            # Update only provided fields
            updates = []
            values = [account_id]
            idx = 2

            if category is not None:
                updates.append(f"category = ${idx}")
                values.append(category)
                idx += 1
            if tags is not None:
                updates.append(f"tags = ${idx}")
                values.append(tags)
                idx += 1
            if notes is not None:
                updates.append(f"notes = ${idx}")
                values.append(notes)
                idx += 1

            if updates:
                updates.append("updated_at = NOW()")
                query = f"UPDATE account_meta SET {', '.join(updates)} WHERE account_id = $1 RETURNING *"
                row = await conn.fetchrow(query, *values)
                return dict(row)
            return dict(existing)
        else:
            # Insert new
            row = await conn.fetchrow("""
                INSERT INTO account_meta (account_id, username, category, tags, notes)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
            """, account_id, username, category or 'unknown', tags or [], notes or '')
            return dict(row)


async def search_accounts(query: str, category: str = None,
                          include_bots: bool = False) -> list[dict]:
    """Search accounts with fuzzy matching on username"""
    pool = await get_pool()

    # Get metadata for merging
    meta_map = await get_all_account_meta()

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Build query with fuzzy matching
            sql = """
                SELECT id, username, email, last_login, online, totaltime,
                       joindate, last_ip, expansion, locked
                FROM account
                WHERE 1=1
            """
            params = []

            # Fuzzy search on username (case-insensitive, contains)
            if query:
                # Simple fuzzy: match if any part matches
                sql += " AND (username LIKE %s OR username LIKE %s OR username LIKE %s)"
                params.extend([
                    f"%{query.upper()}%",  # Contains
                    f"{query.upper()}%",   # Starts with
                    f"%{query.upper()}"    # Ends with
                ])

            if not include_bots:
                sql += " AND username NOT LIKE 'RNDBOT%'"

            sql += " ORDER BY CASE WHEN username = %s THEN 0 WHEN username LIKE %s THEN 1 ELSE 2 END, username"
            params.extend([query.upper(), f"{query.upper()}%"])

            await cur.execute(sql, params)
            rows = await cur.fetchall()

            # Merge with metadata and filter by category
            results = []
            for row in rows:
                account = dict(row)
                meta = meta_map.get(account['id'], {})
                account['category'] = meta.get('category', 'unknown')
                account['tags'] = meta.get('tags', [])
                account['notes'] = meta.get('notes', '')

                # Filter by category if specified
                if category and account['category'] != category:
                    # Auto-categorize bots if not set
                    if category == 'bot' and account['username'].startswith('RNDBOT'):
                        pass  # Include it
                    else:
                        continue

                results.append(account)

            return results


async def get_accounts_with_meta(include_bots: bool = True,
                                  category: str = None) -> list[dict]:
    """Get accounts merged with metadata"""
    pool = await get_pool()
    meta_map = await get_all_account_meta()

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            if include_bots:
                await cur.execute("""
                    SELECT id, username, email, last_login, online, totaltime,
                           joindate, last_ip, expansion, locked
                    FROM account ORDER BY id
                """)
            else:
                await cur.execute("""
                    SELECT id, username, email, last_login, online, totaltime,
                           joindate, last_ip, expansion, locked
                    FROM account WHERE username NOT LIKE 'RNDBOT%%'
                    ORDER BY id
                """)

            rows = await cur.fetchall()
            results = []

            for row in rows:
                account = dict(row)
                meta = meta_map.get(account['id'], {})
                account['category'] = meta.get('category',
                    'bot' if account['username'].startswith('RNDBOT') else 'unknown')
                account['tags'] = meta.get('tags', [])
                account['notes'] = meta.get('notes', '')

                if category and account['category'] != category:
                    continue

                results.append(account)

            return results
