from fastapi import APIRouter, HTTPException, status
from app.models.auth import LoginRequest, TokenResponse
from app.services.auth_service import auth_service
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate with static password and get access token
    """
    access_token = auth_service.authenticate(request.password)
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes
    )

@router.post("/verify")
async def verify_token(token: str):
    """
    Verify if a token is valid
    """
    try:
        payload = auth_service.verify_token(token)
        return {
            "valid": True,
            "user": payload.get("sub"),
            "expires": payload.get("exp")
        }
    except HTTPException:
        return {"valid": False}
