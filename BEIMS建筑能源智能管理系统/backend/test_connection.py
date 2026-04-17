import requests

try:
    response = requests.get('http://localhost:8000/')
    print('成功连接到后端服务:', response.json())
except Exception as e:
    print('无法连接到后端服务:', str(e))

print('测试完成')