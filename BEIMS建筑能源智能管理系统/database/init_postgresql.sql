-- BEIMS 建筑能源智能管理系统 - PostgreSQL 数据库初始化脚本

-- 创建数据库
CREATE DATABASE building_energy;

-- 连接到数据库
\c building_energy;

-- 创建扩展（如果需要）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建用户（可选）
-- CREATE USER beims_user WITH PASSWORD 'your_password';
-- GRANT ALL PRIVILEGES ON DATABASE building_energy TO beims_user;

-- 验证数据库创建
SELECT current_database();

-- 提示
\echo '✅ 数据库 building_energy 创建成功！'
\echo ''
\echo '下一步：'
\echo '1. 修改 backend/.env 文件中的数据库连接字符串'
\echo '2. 运行 backend/start.bat 启动后端服务'
\echo '3. 系统会自动创建所需的数据表'
