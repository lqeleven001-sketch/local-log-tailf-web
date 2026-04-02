# -*- coding: utf-8 -*-
import os
import asyncio
import json
import signal
from aiohttp import web
from aiohttp import web_ws
import paramiko

class LogTailServer:
    def __init__(self):
        self.config = self.load_config()
        self.servers = {s['host']: s for s in self.config.get('servers', [])}
        self.ssh_clients = {}

    def load_config(self):
        """加载配置文件"""
        config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"警告：配置文件 {config_file} 不存在，使用默认配置")
            return {
                'servers': [
                    {
                        'host': '192.168.0.10',
                        'username': 'root',
                        'password': '',
                        'base_path': '/data/logs'
                    }
                ]
            }

    def get_ssh_client(self, server_ip):
        """获取或创建 SSH 连接"""
        if server_ip not in self.ssh_clients:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            server_info = self.servers.get(server_ip)
            if not server_info:
                return None

            try:
                connect_kwargs = {
                    'hostname': server_info['host'],
                    'username': server_info['username'],
                    'port': server_info.get('port', 22),
                    'timeout': 10
                }

                if server_info.get('key_file') and os.path.exists(server_info['key_file']):
                    connect_kwargs['key_filename'] = server_info['key_file']
                elif server_info.get('password'):
                    connect_kwargs['password'] = server_info['password']

                client.connect(**connect_kwargs)
                self.ssh_clients[server_ip] = client
            except Exception as e:
                print(f"SSH 连接失败：{e}")
                return None

        return self.ssh_clients[server_ip]

    async def list_files(self, request):
        """列出目录中的文件"""
        server = request.query.get('server', '')
        path = request.query.get('path', '/data/logs')

        if not server:
            return web.json_response({
                'success': False,
                'message': '未选择服务器'
            })

        try:
            client = self.get_ssh_client(server)
            if not client:
                return web.json_response({
                    'success': False,
                    'message': '无法连接到服务器'
                })

            stdin, stdout, stderr = client.exec_command(f'ls -la "{path}"')
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')

            if error:
                return web.json_response({
                    'success': False,
                    'message': error
                })

            files = []
            for line in output.strip().split('\n')[1:]:
                if line:
                    parts = line.split()
                    if len(parts) >= 9:
                        permissions = parts[0]
                        name = ' '.join(parts[8:])

                        if name in ['.', '..']:
                            continue

                        file_type = 'directory' if permissions[0] == 'd' else 'file'
                        files.append({
                            'name': name,
                            'type': file_type,
                            'permissions': permissions,
                            'size': parts[4] if len(parts) > 4 else '',
                            'modified': ' '.join(parts[5:8]) if len(parts) > 7 else ''
                        })

            return web.json_response({
                'success': True,
                'data': files
            })

        except Exception as e:
            return web.json_response({
                'success': False,
                'message': str(e)
            })

    async def tail_file(self, request):
        """WebSocket 实时查看日志"""
        print("接收到 WebSocket 连接请求")
        ws = web_ws.WebSocketResponse()
        await ws.prepare(request)

        server = request.query.get('server', '')
        file_path = request.query.get('file', '')
        lines = request.query.get('lines', '100')  # 默认显示 100 行

        print(f"WebSocket 请求参数：server={server}, file={file_path}, lines={lines}")

        if not server or not file_path:
            print("WebSocket 请求缺少参数")
            await ws.send_json({
                'success': False,
                'message': '缺少参数'
            })
            await ws.close()
            return ws

        stdin = None
        stdout = None
        stderr = None
        channel = None
        client = None
        tail_cmd = None

        try:
            client = self.get_ssh_client(server)
            if not client:
                print("无法连接到服务器")
                await ws.send_json({
                    'success': False,
                    'message': '无法连接到服务器'
                })
                await ws.close()
                return ws

            # 先获取历史日志（指定行数）
            print(f"执行命令：tail -n {lines} '{file_path}'")
            _stdin, _stdout, _stderr = client.exec_command(f'tail -n {lines} "{file_path}"')
            history_output = _stdout.read().decode('utf-8')
            _stdin.close()
            _stdout.close()
            _stderr.close()

            if history_output:
                print(f"发送历史日志：{len(history_output.splitlines())} 行")
                await ws.send_json({
                    'success': True,
                    'content': history_output
                })

            # 然后开始实时监控 - 使用 bash 包装，确保 channel 关闭时 tail 进程终止
            print(f"执行命令：tail -f '{file_path}'")
            stdin, stdout, stderr = client.exec_command(f'bash -c "tail -f \\"{file_path}\\""')

            async def read_stdout():
                try:
                    while True:
                        line = await asyncio.get_event_loop().run_in_executor(
                            None, stdout.readline
                        )
                        if not line:
                            break
                        print(f"读取到日志行：{line.strip()}")
                        await ws.send_json({
                            'success': True,
                            'content': line
                        })
                except Exception as e:
                    print(f"读取日志错误：{e}")

            await read_stdout()

        except Exception as e:
            print(f"WebSocket 错误：{e}")
            await ws.send_json({
                'success': False,
                'message': str(e)
            })
        finally:
            # 清理资源：关闭 stream
            try:
                if stdin: stdin.close()
                if stdout: stdout.close()
                if stderr: stderr.close()
            except:
                pass

            print("WebSocket 连接关闭，资源已清理")
            await ws.close()

        return ws

    async def download_file(self, request):
        """下载文件"""
        server = request.query.get('server', '')
        file_path = request.query.get('file', '')

        print(f"下载文件请求：server={server}, file={file_path}")

        if not server or not file_path:
            return web.json_response({
                'success': False,
                'message': '缺少参数'
            })

        try:
            client = self.get_ssh_client(server)
            if not client:
                return web.json_response({
                    'success': False,
                    'message': '无法连接到服务器'
                })

            # 使用 SFTP 下载文件
            sftp = client.open_sftp()
            file_content = sftp.file(file_path, 'rb').read()
            sftp.close()

            # 获取文件名
            filename = file_path.split('/')[-1]

            # 返回文件内容
            return web.Response(
                body=file_content,
                content_type='application/octet-stream',
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }
            )

        except Exception as e:
            print(f"下载文件错误：{e}")
            return web.json_response({
                'success': False,
                'message': str(e)
            })

    async def stop(self, request):
        """停止监控"""
        server = request.query.get('server', '')
        if server and server in self.ssh_clients:
            try:
                self.ssh_clients[server].close()
                del self.ssh_clients[server]
            except:
                pass

        return web.json_response({'success': True})

    async def get_servers(self, request):
        """获取服务器列表"""
        servers = []
        for host, info in self.servers.items():
            servers.append({
                'host': host,
                'name': info.get('name', host),
                'base_path': info.get('base_path', '/data/logs')
            })

        return web.json_response({
            'success': True,
            'servers': servers
        })

    def create_app(self):
        app = web.Application()

        # 调试：打印当前工作目录
        print(f"当前工作目录：{os.getcwd()}")
        print(f"index.html 是否存在：{os.path.exists('index.html')}")

        # 根路径处理
        async def handle_root(request):
            print(f"处理根路径请求：{request.url}")
            try:
                return web.FileResponse('index.html')
            except Exception as e:
                print(f"根路径处理错误：{e}")
                return web.Response(text=f"Error: {e}", status=500)

        # 添加路由
        app.add_routes([
            web.get('/', handle_root),
            web.get('/api/servers', self.get_servers),
            web.get('/api/files/list', self.list_files),
            web.get('/api/files/download', self.download_file),
            web.get('/api/tail', self.tail_file),
            web.post('/api/stop', self.stop),
            web.static('/', '.')
        ])

        return app

def main():
    server = LogTailServer()
    app = server.create_app()

    print("LogTail 服务器启动中...")
    print("访问地址：http://localhost:18081")
    print("按 Ctrl+C 停止服务器")

    # 创建事件循环
    loop = asyncio.get_event_loop()

    # 定义信号处理函数
    def signal_handler(sig, frame):
        print("\n正在停止服务器...")
        # 取消所有任务
        for task in asyncio.all_tasks(loop):
            task.cancel()
        # 关闭事件循环
        loop.stop()

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 运行服务器
    try:
        loop.run_until_complete(web._run_app(app, host='0.0.0.0', port=18081))
    except asyncio.CancelledError:
        print("服务器已停止")
    finally:
        # 关闭所有 SSH 连接
        for client in server.ssh_clients.values():
            try:
                client.close()
            except:
                pass
        # 关闭事件循环
        loop.close()

if __name__ == '__main__':
    main()
