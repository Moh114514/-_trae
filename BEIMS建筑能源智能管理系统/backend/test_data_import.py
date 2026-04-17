"""
数据导入测试脚本
直接测试数据导入功能，不通过HTTP接口
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import SessionLocal, init_db
from app.services.data_processor import DataProcessor
import pandas as pd

def test_data_import():
    print("=" * 60)
    print("BEIMS 数据导入测试")
    print("=" * 60)
    print()
    
    csv_file = os.path.join("..", "Dataset", "SHIFDR_Structured_Energy_Dataset.csv")
    
    if not os.path.exists(csv_file):
        print(f"❌ 数据文件不存在: {csv_file}")
        return False
    
    print(f"数据文件: {csv_file}")
    print(f"文件大小: {os.path.getsize(csv_file) / 1024 / 1024:.2f} MB")
    print()
    
    db = SessionLocal()
    processor = DataProcessor(db)
    
    try:
        print("步骤 1: 加载CSV数据...")
        df = processor.load_csv_data(csv_file)
        print(f"✅ 加载完成，共 {len(df)} 行数据")
        print()
        
        print("步骤 2: 数据清洗...")
        df = processor.clean_data(df)
        print(f"✅ 清洗完成，剩余 {len(df)} 行数据")
        print()
        
        print("步骤 3: 数据标准化...")
        df = processor.standardize_data(df)
        print("✅ 标准化完成")
        print()
        
        print("步骤 4: 数据验证...")
        is_valid, errors, warnings = processor.validate_data(df)
        
        if not is_valid:
            print("❌ 数据验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        print("✅ 数据验证通过")
        print()
        
        print("步骤 5: 导入数据库...")
        print("这可能需要几分钟，请耐心等待...")
        print()
        
        records_count = processor.import_to_database(df, batch_size=500)
        
        print()
        print("=" * 60)
        print(f"✅ 导入成功！共导入 {records_count} 条记录")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ 导入失败: {str(e)}")
        print("=" * 60)
        
        import traceback
        traceback.print_exc()
        
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print()
    success = test_data_import()
    print()
    
    if success:
        print("🎉 数据导入测试成功！")
        print()
        print("下一步:")
        print("  1. 启动后端服务: python -m app.main")
        print("  2. 启动前端服务: cd ../frontend && npm run dev")
        print("  3. 访问系统: http://localhost:3000")
    else:
        print("❌ 数据导入测试失败，请检查错误信息")
    
    print()
    input("按回车键退出...")
