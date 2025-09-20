from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .logging import get_logger
from ..services.user_service import UserService

logger = get_logger("core.auth")

# 創建 HTTPBearer 實例
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    從 JWT token 中獲取當前用戶
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 解碼 JWT token
        payload = jwt.decode(
            credentials.credentials, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        logger.warning("JWT token validation failed")
        raise credentials_exception
    
    # 從資料庫獲取用戶信息
    user_service = UserService(db)
    user = user_service.get_user_by_username(username)
    if user is None:
        logger.warning("User not found in database", username=username)
        raise credentials_exception
    
    logger.debug("User authenticated successfully", username=username, user_id=user.id)
    return user

def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    可選的用戶認證，如果沒有 token 或 token 無效則返回 None
    """
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None
