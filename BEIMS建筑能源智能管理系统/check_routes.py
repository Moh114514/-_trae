import re

with open('frontend/dist/assets/index-DD4bMhDJ.js', 'r', encoding='utf-8') as f:
    content = f.read()
    
# 查找路由配置
routes = re.findall(r'path\s*[=:]\s*["\']([^"\']+)["\']', content)
print('Routes found:', len(routes))
for r in routes[:20]:
    print(r)
