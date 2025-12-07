"""
Account management API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services import accounts

router = APIRouter(prefix="/accounts", tags=["accounts"])


class CreateAccountRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = ""


class SetGmLevelRequest(BaseModel):
    gm_level: int
    realm_id: int = -1


class ChangePasswordRequest(BaseModel):
    password: str


class SetAccountMetaRequest(BaseModel):
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    notes: Optional[str] = None


@router.get("")
async def list_accounts(include_bots: bool = False, category: Optional[str] = None):
    """List all accounts with metadata"""
    account_list = await accounts.get_accounts_with_meta(
        include_bots=include_bots,
        category=category
    )
    return {"accounts": account_list}


@router.get("/search")
async def search_accounts(
    q: str = "",
    category: Optional[str] = None,
    include_bots: bool = False
):
    """Search accounts with fuzzy matching"""
    results = await accounts.search_accounts(
        query=q,
        category=category,
        include_bots=include_bots
    )
    return {"accounts": results, "query": q}


@router.get("/categories")
async def get_categories():
    """Get available account categories"""
    return {"categories": accounts.CATEGORIES}


@router.get("/stats")
async def get_stats():
    """Get account statistics"""
    return await accounts.get_account_stats()


@router.get("/online")
async def get_online():
    """Get currently online accounts"""
    online_list = await accounts.get_online_accounts()
    return {"online": online_list}


@router.get("/{account_id}")
async def get_account(account_id: int):
    """Get account details"""
    account = await accounts.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.get("/{account_id}/characters")
async def get_characters(account_id: int):
    """Get characters for an account"""
    chars = await accounts.get_account_characters(account_id)
    return {"characters": chars}


@router.post("")
async def create_account(request: CreateAccountRequest):
    """Create a new account"""
    if len(request.username) < 3:
        raise HTTPException(status_code=400, detail="Username too short")
    if len(request.password) < 4:
        raise HTTPException(status_code=400, detail="Password too short")

    result = await accounts.create_account(
        request.username,
        request.password,
        request.email or ""
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create account"))

    return result


@router.get("/{account_id}/gmlevel")
async def get_gm_level(account_id: int):
    """Get GM level for an account"""
    level = await accounts.get_account_gm_level(account_id)
    return {"gm_level": level}


@router.post("/{account_id}/gmlevel")
async def set_gm_level(account_id: int, request: SetGmLevelRequest):
    """Set GM level for an account"""
    success = await accounts.set_account_gm_level(
        account_id,
        request.gm_level,
        request.realm_id
    )
    return {"success": success}


@router.post("/{account_id}/password")
async def change_password(account_id: int, request: ChangePasswordRequest):
    """Change password for an account"""
    if len(request.password) < 4:
        raise HTTPException(status_code=400, detail="Password too short (min 4 chars)")

    result = await accounts.change_password(account_id, request.password)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to change password"))

    return result


@router.get("/{account_id}/meta")
async def get_account_meta(account_id: int):
    """Get account metadata"""
    meta = await accounts.get_account_meta(account_id)
    return meta or {"account_id": account_id, "category": "unknown", "tags": [], "notes": ""}


@router.put("/{account_id}/meta")
async def set_account_meta(account_id: int, request: SetAccountMetaRequest):
    """Set account metadata (category, tags, notes)"""
    # Get account to get username
    account = await accounts.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    result = await accounts.set_account_meta(
        account_id=account_id,
        username=account['username'],
        category=request.category,
        tags=request.tags,
        notes=request.notes
    )
    return result
