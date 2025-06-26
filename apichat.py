from http.server import BaseHTTPRequestHandler
import json
import requests
import os
import traceback

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 检查路径
            if self.path == '/api/chat' or self.path == '/chat':
                # 读取请求数据
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    self.send_error_response(400, "Empty request body")
                    return
                
                post_data = self.rfile.read(content_length)
                
                try:
                    data = json.loads(post_data.decode('utf-8'))
                except json.JSONDecodeError as e:
                    self.send_error_response(400, f"Invalid JSON: {str(e)}")
                    return
                
                user_message = data.get('message', '').strip()
                if not user_message:
                    self.send_error_response(400, "Message is required")
                    return
                
                # 调用扣子API
                result = self.call_coze_api(user_message)
                
                if result:
                    self.send_success_response(result)
                else:
                    self.send_error_response(500, "Failed to get response from Coze API")
            else:
                self.send_error_response(404, "Endpoint not found")
                
        except Exception as e:
            print(f"Handler error: {str(e)}")
            traceback.print_exc()
            self.send_error_response(500, f"Internal server error: {str(e)}")
    
    def call_coze_api(self, message):
        """调用扣子API"""
        url = "https://api.coze.cn/v3/chat"
        headers = {
            'Authorization': 'Bearer cztei_l60uwQX6h9ZjTLExF1SWuqOPW47hufRoDjIvfs7pqQrToEE2kRYfArn1Ndsl4matq',
            'Content-Type': 'application/json',
            'User-Agent': 'Vercel-Function/1.0'
        }
        
        payload = {
            "bot_id": "7513006974863310889",
            "user_id": "web_user",
            "stream": False,
            "auto_save_history": True,
            "additional_messages": [
                {
                    "role": "user",
                    "content": message,
                    "content_type": "text"
                }
            ]
        }
        
        try:
            print(f"Calling Coze API with message: {message[:50]}...")
            
            response = requests.post(
                url, 
                headers=headers, 
                json=payload,
                timeout=30  # 添加超时
            )
            
            print(f"Coze API response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("Coze API call successful")
                return result
            else:
                print(f"Coze API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("Coze API timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Coze API request error: {str(e)}")
            return None
        except Exception as e:
            print(f"Coze API unexpected error: {str(e)}")
            return None
    
    def send_success_response(self, data):
        """发送成功响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        
        response_data = {
            "success": True,
            "data": data
        }
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
    
    def send_error_response(self, status_code, message):
        """发送错误响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        
        error_data = {
            "success": False,
            "error": message,
            "status_code": status_code
        }
        self.wfile.write(json.dumps(error_data, ensure_ascii=False).encode('utf-8'))
    
    def do_OPTIONS(self):
        """处理预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS, GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '3600')
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求 - 用于健康检查"""
        if self.path == '/api/health' or self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            health_data = {
                "status": "healthy",
                "service": "Coze API Proxy",
                "timestamp": requests.utils.datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_error_response(404, "GET endpoint not found")

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.date_time_string()}] {format % args}")
