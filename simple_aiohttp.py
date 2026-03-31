from aiohttp import web

async def handle(request):
    print(f"接收到请求: {request.url}")
    return web.Response(text="Hello, aiohttp!")

app = web.Application()
app.add_routes([web.get('/', handle)])

print("简单 aiohttp 服务器启动在 http://localhost:18083")
web.run_app(app, host='0.0.0.0', port=18083)
