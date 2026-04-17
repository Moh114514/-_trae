"""
数据库初始化脚本
运行此脚本以创建所有必要的数据表
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import Base, engine, SessionLocal
from app.config.settings import settings

def init_database():
    print("=" * 50)
    print("BEIMS 数据库初始化")
    print("=" * 50)
    print()
    
    print(f"数据库类型: {'SQLite' if 'sqlite' in settings.DATABASE_URL else 'PostgreSQL'}")
    print(f"数据库URL: {settings.DATABASE_URL}")
    print()
    
    print("正在创建数据表...")
    
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ 数据表创建成功！")
        print()
        
        print("已创建的数据表:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
        
        print()
        print("=" * 50)
        print("数据库初始化完成！")
        print("=" * 50)
        
        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    print()
    print("测试数据库连接...")
    
    try:
        db = SessionLocal()
        
        from app.models.database import EnergyData
        count = db.query(EnergyData).count()
        
        print(f"✅ 数据库连接成功！")
        print(f"当前数据记录数: {count}")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_database()
    
    if success:
        test_database_connection()
    
    print()
    input("按回车键退出...")
