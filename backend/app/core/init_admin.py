from sqlalchemy.orm import Session
from .database import SessionLocal
from .security import get_password_hash
from ..models.user import User


def create_admin_user():
    """創建管理員帳號"""
    db = SessionLocal()
    try:
        # 檢查是否已存在 admin 使用者
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("Admin user already exists")
            return existing_admin
        
        # 創建 admin 使用者
        admin_user = User(
            username="admin",
            hashed_password=get_password_hash("admin"),  # 預設密碼
            is_active=True,
            is_superuser=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("Admin user created successfully")
        print(f"Username: admin")
        print(f"Password: admin123")
        print("Please change the password after first login!")
        
        return admin_user
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
        return None
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
