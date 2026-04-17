from app.models.database import get_db, EnergyData

# 获取数据库连接
db = next(get_db())

try:
    # 查询前5条数据
    sample = db.query(EnergyData).limit(5).all()
    print('样本数据:')
    for s in sample:
        print(f'ID: {s.id}, Building: {s.building_id}, Occupancy: {s.occupancy_density}, Meter: {s.meter_id}')
    
    # 统计有值的记录数
    total_records = db.query(EnergyData).count()
    occupancy_not_null = db.query(EnergyData).filter(EnergyData.occupancy_density.isnot(None)).count()
    meter_not_null = db.query(EnergyData).filter(EnergyData.meter_id.isnot(None)).count()
    
    print(f'\n统计信息:')
    print(f'总记录数: {total_records}')
    print(f'人员密度不为空的记录数: {occupancy_not_null}')
    print(f'仪表ID不为空的记录数: {meter_not_null}')
finally:
    db.close()