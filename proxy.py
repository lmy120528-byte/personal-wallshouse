#!/usr/bin/env python3
"""
本地 API 代理 —— 解决浏览器 CORS 跨域限制
将管理工具的请求转发到 DeepSeek API

用法：python3 proxy.py
默认端口 8081，管理工具会自动连接
"""

import http.server
import json
import urllib.request
import urllib.error
import os

PROXY_PORT = 8081
DEEPSEEK_API = 'https://api.deepseek.com/v1/chat/completions'

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        """转发 POST 请求到 DeepSeek API"""
        if self.path != '/analyze':
            self.send_response(404)
            self._cors_headers()
            self.end_headers()
            return

        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            req_data = json.loads(body)

            api_key = req_data.pop('api_key', '')
            if not api_key:
                self._error(400, '缺少 api_key')
                return

            # 转发到 DeepSeek
            http_req = urllib.request.Request(
                DEEPSEEK_API,
                data=json.dumps(req_data).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                }
            )

            with urllib.request.urlopen(http_req) as resp:
                resp_body = resp.read()
                self.send_response(resp.status)
                self._cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(resp_body)

        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='replace')
            self._error(e.code, err_body[:500])
        except Exception as e:
            self._error(500, str(e))

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _error(self, code, msg):
        self.send_response(code)
        self._cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        err = json.dumps({'error': msg}).encode('utf-8')
        self.wfile.write(err)

    def log_message(self, format, *args):
        print(f'[proxy] {args[0]}')

if __name__ == '__main__':
    print(f'代理已启动 → http://localhost:{PROXY_PORT}/analyze')
    print('管理工具会通过此代理调用 DeepSeek API')
    print('按 Ctrl+C 停止\n')
    http.server.HTTPServer(('', PROXY_PORT), ProxyHandler).serve_forever()
