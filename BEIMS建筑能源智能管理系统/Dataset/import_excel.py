import pandas as pd
from sqlalchemy import create_engine, inspect

# 1. 数据库连接设置
engine = create_engine('postgresql://postgres:123456@localhost:5432/building_energy')

def import_new_dataset(file_path):
    print("读取新数据集中...")
    # 如果是CSV用 pd.read_csv，如果是Excel用 pd.read_excel
    df = pd.read_csv(file_path)

    # 2. 建立精准映射（左边是你的Excel表头，右边是数据库字段）
    column_mapping = {
        'Building_ID': 'building_id',
        'Building_Type': 'building_type',
        'Timestamp': 'timestamp',
        'Electricity_Consumption_kWh': 'electricity_kwh',
        'Water_Consumption_m3': 'water_m3',
        'HVAC_Energy_kWh': 'hvac_kwh',
        'CHW_Supply_Temp_C': 'chw_supply_temp',
        'CHW_Return_Temp_C': 'chw_return_temp',
        'Outdoor_Temp_C': 'outdoor_temp',
        'Relative_Humidity_Pct': 'humidity_pct',
        'Occupancy_Density_People_100qm': 'occupancy_density',
        'Meter_ID': 'meter_id',
        'System_Status': 'system_status'
    }

    missing_source_columns = [column for column in column_mapping if column not in df.columns]
    if missing_source_columns:
        raise ValueError(f"源数据缺少必要列: {missing_source_columns}")
    
    # 重命名列
    df_mapped = df.rename(columns=column_mapping)

    # 兼容数据库历史字段名差异：building_id -> building_name
    target_columns = {column['name'] for column in inspect(engine).get_columns('energy_reports')}
    if 'building_id' in df_mapped.columns and 'building_id' not in target_columns and 'building_name' in target_columns:
        df_mapped = df_mapped.rename(columns={'building_id': 'building_name'})

    matched_columns = [column for column in df_mapped.columns if column in target_columns]
    if not matched_columns:
        raise ValueError("源数据字段与 energy_reports 表结构完全不匹配，请检查列映射或数据库表定义。")

    skipped_columns = [column for column in df_mapped.columns if column not in target_columns]
    if skipped_columns:
        print(f"跳过数据库中不存在的字段: {skipped_columns}")

    df_final = df_mapped[matched_columns].copy()

    # 3. 处理时间格式（处理 Excel 常见的格式问题）
    if 'timestamp' in df_final.columns:
        df_final['timestamp'] = pd.to_datetime(df_final['timestamp'])

    # 4. 导入数据库
    print("数据写入中，请稍候...")
    df_final.to_sql('energy_reports', engine, if_exists='append', index=False, chunksize=5000)
    print("✅ 数据库已成功更新为最新数据集！")

if __name__ == "__main__":
    import_new_dataset('SHIFDR_Structured_Energy_Dataset.csv') # 替换为你的文件名