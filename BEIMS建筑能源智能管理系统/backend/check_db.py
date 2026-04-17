import sqlite3

# 连接到数据库
conn = sqlite3.connect('beims.db')
cursor = conn.cursor()

# 检查energy_data表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='energy_data';")
table_exists = cursor.fetchone()

if table_exists:
    print("energy_data表存在")
    
    # 检查表中的数据量
    cursor.execute("SELECT COUNT(*) FROM energy_data;")
    count = cursor.fetchone()[0]
    print(f"表中有 {count} 条记录")
    
    # 检查表结构
    print("\n表结构:")
    cursor.execute("PRAGMA table_info(energy_data);")
    columns = cursor.fetchall()
    for column in columns:
        print(f"{column[1]}: {column[2]}")
    
    # 检查前5条记录
    print("\n前5条记录:")
    cursor.execute("SELECT * FROM energy_data LIMIT 5;")
    records = cursor.fetchall()
    for record in records:
        print(record)
else:
    print("energy_data表不存在")

# 关闭连接
conn.close()