from sqlalchemy.orm import Session
from typing import Optional, List
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from ..core.logging import get_logger

logger = get_logger("services.user")


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: int) -> Optional[User]:
        """根據 ID 獲取使用者"""
        logger.debug("Getting user by ID", user_id=user_id)
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            logger.debug("User found", user_id=user_id, username=user.username)
        else:
            logger.debug("User not found", user_id=user_id)
        return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        """根據使用者名稱獲取使用者"""
        logger.debug("Getting user by username", username=username)
        user = self.db.query(User).filter(User.username == username).first()
        if user:
            logger.debug("User found by username", username=username, user_id=user.id)
        else:
            logger.debug("User not found by username", username=username)
        return user

    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """獲取使用者列表"""
        logger.debug("Getting users list", skip=skip, limit=limit)
        users = self.db.query(User).offset(skip).limit(limit).all()
        logger.debug("Users list retrieved", count=len(users))
        return users

    def create_user(self, user: UserCreate) -> User:
        """創建新使用者"""
        logger.info("Creating new user", username=user.username)
        try:
            db_user = User(
                username=user.username,
                is_active=user.is_active
            )
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            logger.info("User created successfully", user_id=db_user.id, username=db_user.username)
            return db_user
        except Exception as e:
            logger.error("Failed to create user", username=user.username, error=str(e), exc_info=True)
            self.db.rollback()
            raise

    def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """更新使用者資訊"""
        logger.info("Updating user", user_id=user_id)
        db_user = self.get_user(user_id)
        if not db_user:
            logger.warning("User not found for update", user_id=user_id)
            return None

        try:
            update_data = user_update.dict(exclude_unset=True)

            for field, value in update_data.items():
                setattr(db_user, field, value)
                logger.debug("User field updated", user_id=user_id, field=field)

            self.db.commit()
            self.db.refresh(db_user)
            logger.info("User updated successfully", user_id=user_id, username=db_user.username)
            return db_user
        except Exception as e:
            logger.error("Failed to update user", user_id=user_id, error=str(e), exc_info=True)
            self.db.rollback()
            raise

    def delete_user(self, user_id: int) -> bool:
        """刪除使用者"""
        logger.info("Deleting user", user_id=user_id)
        db_user = self.get_user(user_id)
        if not db_user:
            logger.warning("User not found for deletion", user_id=user_id)
            return False

        try:
            username = db_user.username
            self.db.delete(db_user)
            self.db.commit()
            logger.info("User deleted successfully", user_id=user_id, username=username)
            return True
        except Exception as e:
            logger.error("Failed to delete user", user_id=user_id, error=str(e), exc_info=True)
            self.db.rollback()
            raise

