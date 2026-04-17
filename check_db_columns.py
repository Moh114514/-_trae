import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432, database='building_energy', 
    user='postgres', password='416417'
)
cur = conn.cursor()

# 查询表结构
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name='energy_reports'
    ORDER BY ordinal_position
""")
columns = cur.fetchall()

print("数据库实际字段：")
for col, dtype in columns:
    print(f"  {col} ({dtype})")

cur.close()
conn.close()