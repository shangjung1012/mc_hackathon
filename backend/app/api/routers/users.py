from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...core.logging import get_logger
from ...schemas.user import User, UserCreate, UserUpdate
from ...services.user_service import UserService

logger = get_logger("api.users")

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """創建新使用者"""
    logger.info("User creation attempt", username=user.username)
    
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
        logger.info("User created successfully", user_id=new_user.id, username=new_user.username)
        return new_user
    except Exception as e:
        logger.error("User creation failed", username=user.username, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


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
    db: Session = Depends(get_db)
):
    """更新使用者資訊"""
    logger.info("User update attempt", user_id=user_id)
    
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
    db: Session = Depends(get_db)
):
    """刪除使用者"""
    logger.info("User deletion attempt", user_id=user_id)
    
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
