import http.server
import urllib.request
import urllib.parse
import socketserver
import ssl
from socketserver import ThreadingMixIn

PORT = 8000
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

class ThreadedHTTPServer(ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

class VWorldProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # 🧪 자가 치유형 프록시 엔진 (Auto-Repair)
        if self.path.startswith('/proxy'):
            try:
                # 1. 쿼리 파라미터 분해
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)
                
                target_url = params.get('url', [None])[0]
                if not target_url: return

                # 2. OpenLayers가 붙인 나머지 파라미터들 수집
                others = {k: v[0] for k, v in params.items() if k != 'url'}
                
                # 3. URL 재조립 (핵심: ?와 & 자동 교정)
                if others:
                    conn = "&" if "?" in target_url else "?"
                    target_url = f"{target_url}{conn}{urllib.parse.urlencode(others)}"

                # 4. 도메인 세탁 중지 (클라이언트가 보낸 도메인 그대로 사용)
                # target_url = target_url.replace('domain=localhost', 'domain=map.vworld.kr') 
                # 위 로직이 오히려 인증 에러를 유발할 수 있어 주석 처리합니다.

                # 4. 공백 및 특수문자 안전 처리 (urllib은 공백을 허용하지 않음)
                target_url = target_url.replace(' ', '%20')

                # DEBUG: 서버가 도대체 어디로 가려고 하는지 출력 (원인 분석용)
                print(f"📡 Forwarding to: {target_url[:150]}...")

                headers = {
                    'Referer': 'https://map.vworld.kr/',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Origin': 'https://map.vworld.kr'
                }
                
                req = urllib.request.Request(target_url, headers=headers)
                with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                    self.send_response(200)
                    self.send_header('Content-type', response.info().get_content_type())
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(response.read())
            except urllib.error.HTTPError as e:
                print(f"⚠️ VWorld API Error: {e.code} for {target_url[:50]}")
                self.send_response(e.code)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(str(e.reason).encode())
            except Exception as e:
                print(f"❌ Proxy Critical Error: {e}")
                self.send_response(500)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(str(e).encode())
            return

        super().do_GET()

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with ThreadedHTTPServer(("", PORT), VWorldProxyHandler) as httpd:
        print(f"🚀 Auto-Repair Server started at http://localhost:{PORT}")
        httpd.serve_forever()
