from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from ...core.database import get_db
from ...core.logging import get_logger
from ...core.config import settings
from ...schemas.user import User, UserCreate, UserUpdate, Token
from ...services.user_service import UserService

logger = get_logger("api.users")

router = APIRouter(prefix="/users", tags=["users"])


def create_access_token(data: dict, expires_delta: timedelta = None):
    """創建 JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.now(datetime.timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


@router.post("/register", response_model=dict)
def register_user(username: str, db: Session = Depends(get_db)):
    """註冊新使用者（無密碼）"""
    logger.debug("User registration attempt", username=username)
    
    user_service = UserService(db)
    
    # 檢查使用者名稱是否已存在
    if user_service.get_user_by_username(username):
        logger.warning("User registration failed: username already exists", username=username)
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )
    
    try:
        # 創建用戶
        user_data = UserCreate(username=username)
        new_user = user_service.create_user(user_data)
        
        # 創建 token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": new_user.username}, expires_delta=access_token_expires
        )
        
        logger.debug("User registered successfully", user_id=new_user.id, username=new_user.username)
        return {
            "success": True,
            "message": "User registered successfully",
            "user": new_user,
            "token": access_token
        }
    except Exception as e:
        logger.error("User registration failed", username=username, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login", response_model=dict)
def login_user(username: str, db: Session = Depends(get_db)):
    """使用者登入（無密碼）"""
    logger.debug("User login attempt", username=username)
    
    user_service = UserService(db)
    user = user_service.get_user_by_username(username)
    
    if not user:
        logger.warning("User login failed: user not found", username=username)
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )
    
    try:
        # 創建 token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        logger.debug("User logged in successfully", user_id=user.id, username=user.username)
        return {
            "success": True,
            "message": "User logged in successfully",
            "user": user,
            "token": access_token
        }
    except Exception as e:
        logger.error("User login failed", username=username, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """創建新使用者"""
    logger.debug("User creation attempt", username=user.username)
    
    user_service = UserService(db)
    
    # 檢查使用者名稱是否已存在
    if user_service.get_user_by_username(user.username):
        logger.warning("User creation failed: username already exists", username=user.username)
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )
    
    try:
        new_user = user_service.create_user(user)
        logger.debug("User created successfully", user_id=new_user.id, username=new_user.username)
        return new_user
    except Exception as e:
        logger.error("User creation failed", username=user.username, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """獲取使用者列表"""
    logger.debug("Users list requested", skip=skip, limit=limit)
    user_service = UserService(db)
    users = user_service.get_users(skip=skip, limit=limit)
    logger.debug("Users list retrieved", count=len(users))
    return users


@router.get("/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """根據 ID 獲取使用者"""
    logger.debug("User details requested", user_id=user_id)
    user_service = UserService(db)
    user = user_service.get_user(user_id)
    if user is None:
        logger.warning("User not found", user_id=user_id)
        raise HTTPException(status_code=404, detail="User not found")
    logger.debug("User details retrieved", user_id=user_id, username=user.username)
    return user


@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    db: Session = Depends(get_db)
):
    """更新使用者資訊"""
    logger.debug("User update attempt", user_id=user_id)
    
    try:
        user_service = UserService(db)
        user = user_service.update_user(user_id, user_update)
        if user is None:
            logger.warning("User update failed: user not found", user_id=user_id)
            raise HTTPException(status_code=404, detail="User not found")
        logger.debug("User updated successfully", user_id=user_id, username=user.username)
        return user
    except Exception as e:
        logger.error("User update failed", user_id=user_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{user_id}")
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db)
):
    """刪除使用者"""
    logger.debug("User deletion attempt", user_id=user_id)
    
    try:
        user_service = UserService(db)
        if not user_service.delete_user(user_id):
            logger.warning("User deletion failed: user not found", user_id=user_id)
            raise HTTPException(status_code=404, detail="User not found")
        logger.debug("User deleted successfully", user_id=user_id)
        return {"message": "User deleted successfully"}
    except Exception as e:
        logger.error("User deletion failed", user_id=user_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
