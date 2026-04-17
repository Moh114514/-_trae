#!/usr/bin/env python3
"""
创建默认管理员账号（明文密码）
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.database import SessionLocal, User

def create_admin():
    """创建默认管理员账号"""
    print("=" * 50)
    print("创建默认管理员账号")
    print("=" * 50)
    
    # 数据库会话
    db = SessionLocal()
    
    try:
        # 检查是否已存在管理员账号
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("⚠️  管理员账号已存在！")
            print(f"   用户名: {existing_admin.username}")
            print(f"   邮箱: {existing_admin.email}")
            return
        
        # 创建管理员账号（使用明文密码，后续可以通过系统修改）
        admin_user = User(
            username="admin",
            email="admin@example.com",
            full_name="System Administrator",
            hashed_password="admin123",  # 暂时使用明文密码
            role="admin",
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ 管理员账号创建成功！")
        print(f"   用户名: {admin_user.username}")
        print(f"   密码: admin123")
        print(f"   邮箱: {admin_user.email}")
        print(f"   角色: {admin_user.role}")
        print()
        print("请使用以上账号登录系统。")
        print("建议登录后修改默认密码以提高安全性。")
        
    except Exception as e:
        print(f"❌ 创建管理员账号失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
