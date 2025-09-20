from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

from ...core.database import get_db
from ...core.security import create_access_token, verify_token
from ...core.logging import get_logger
from ...schemas.user import User, UserCreate, UserUpdate, UserLogin, Token
from ...services.user_service import UserService
from ...core.config import settings

logger = get_logger("api.users")

router = APIRouter(prefix="/users", tags=["users"])


def get_current_user(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """獲取當前使用者"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_service = UserService(db)
    user = user_service.get_user_by_username(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/register", response_model=User)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """註冊新使用者"""
    logger.info("User registration attempt", username=user.username)
    
    user_service = UserService(db)
    
    # 檢查使用者名稱是否已存在
    if user_service.get_user_by_username(user.username):
        logger.warning("Registration failed: username already exists", username=user.username)
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    try:
        new_user = user_service.create_user(user)
        logger.info("User registered successfully", user_id=new_user.id, username=new_user.username)
        return new_user
    except Exception as e:
        logger.error("User registration failed", username=user.username, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login", response_model=Token)
def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """使用者登入"""
    logger.info("User login attempt", username=user_credentials.username)
    
    user_service = UserService(db)
    user = user_service.authenticate_user(
        user_credentials.username, 
        user_credentials.password
    )
    
    if not user:
        logger.warning("Login failed: invalid credentials", username=user_credentials.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        logger.info("User login successful", user_id=user.id, username=user.username)
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error("Login token creation failed", username=user_credentials.username, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    """獲取當前使用者資訊"""
    logger.info("User profile accessed", user_id=current_user.id, username=current_user.username)
    return current_user


@router.get("/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """獲取使用者列表"""
    logger.info("Users list requested", skip=skip, limit=limit)
    user_service = UserService(db)
    users = user_service.get_users(skip=skip, limit=limit)
    logger.info("Users list retrieved", count=len(users))
    return users


@router.get("/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """根據 ID 獲取使用者"""
    logger.info("User details requested", user_id=user_id)
    user_service = UserService(db)
    user = user_service.get_user(user_id)
    if user is None:
        logger.warning("User not found", user_id=user_id)
        raise HTTPException(status_code=404, detail="User not found")
    logger.info("User details retrieved", user_id=user_id, username=user.username)
    return user


@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新使用者資訊"""
    logger.info("User update attempt", user_id=user_id, current_user_id=current_user.id)
    
    # 只能更新自己的資訊，除非是超級使用者
    if current_user.id != user_id and not current_user.is_superuser:
        logger.warning("User update denied: insufficient permissions", 
                      user_id=user_id, current_user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        user_service = UserService(db)
        user = user_service.update_user(user_id, user_update)
        if user is None:
            logger.warning("User update failed: user not found", user_id=user_id)
            raise HTTPException(status_code=404, detail="User not found")
        logger.info("User updated successfully", user_id=user_id, username=user.username)
        return user
    except Exception as e:
        logger.error("User update failed", user_id=user_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{user_id}")
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """刪除使用者"""
    logger.info("User deletion attempt", user_id=user_id, current_user_id=current_user.id)
    
    # 只有超級使用者可以刪除使用者
    if not current_user.is_superuser:
        logger.warning("User deletion denied: insufficient permissions", 
                      user_id=user_id, current_user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        user_service = UserService(db)
        if not user_service.delete_user(user_id):
            logger.warning("User deletion failed: user not found", user_id=user_id)
            raise HTTPException(status_code=404, detail="User not found")
        logger.info("User deleted successfully", user_id=user_id)
        return {"message": "User deleted successfully"}
    except Exception as e:
        logger.error("User deletion failed", user_id=user_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
