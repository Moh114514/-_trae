import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432, database='building_energy', 
    user='postgres', password='416417'
)
cur = conn.cursor()

# 查询所有表
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
tables = cur.fetchall()
print("数据库中的表:", [t[0] for t in tables])

# 查询第一个表的结构
if tables:
    table_name = tables[0][0]
    cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table_name}'")
    columns = cur.fetchall()
    print(f"\n表 {table_name} 的字段:")
    for col, dtype in columns:
        print(f"  - {col} ({dtype})")
    
    # 查询建筑列表
    cur.execute(f"SELECT DISTINCT building_id FROM {table_name}")
    buildings = cur.fetchall()
    print(f"\n建筑列表: {[b[0] for b in buildings]}")

cur.close()
conn.close()