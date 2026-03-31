from aiohttp import web
import os

async def handle_root(request):
    print(f"处理根路径请求: {request.url}")
    try:
        return web.FileResponse('index.html')
    except Exception as e:
        print(f"根路径处理错误: {e}")
        return web.Response(text=f"Error: {e}", status=500)

async def handle_api_servers(request):
    print(f"处理 API 服务器请求")
    return web.json_response({
        'success': True,
        'servers': [
            {'host': '127.0.0.1', 'name': '测试服务器'}
        ]
    })

app = web.Application()
app.add_routes([
    web.get('/', handle_root),
    web.get('/api/servers', handle_api_servers),
    web.static('/', '.')
])

print("简化版 LogTail 服务器启动在 http://localhost:18084")
print(f"当前目录: {os.getcwd()}")
print(f"index.html 存在: {os.path.exists('index.html')}")

web.run_app(app, host='0.0.0.0', port=18084)
