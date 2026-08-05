import secrets
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.billing import APIKey

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

@router.post("/generate")
async def generate_api_key(
    name: str = "Default Key",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Generate raw key
    raw_key = f"sk_live_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    api_key = APIKey(
        key_hash=key_hash,
        name=name,
        user_id=current_user.id
    )
    db.add(api_key)
    await db.commit()

    return {
        "name": name,
        "api_key": raw_key,  # Sirf ek baar dikhayen
        "message": "Save this key securely. You won't be able to see it again."
    }
