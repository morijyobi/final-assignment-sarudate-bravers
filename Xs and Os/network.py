import socket
import threading

class Network:
    def __init__(self):
        self.conn = None
        self.connected = False
        self.server_waiting = False  # サーバー起動＆待機中フラグ
        self.recv_thread = None
        self.recv_buffer = []
        self.lock = threading.Lock()

    def start_server(self, port=5000):
        server = socket.socket()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", port))
        server.listen(1)
        self.server_waiting = True  # 接続待機中フラグON
        print("[Network] サーバー起動・接続待機中")  # ← ここで表示！
        self.conn, addr = server.accept()
        print("クライアントが接続:", addr)
        self.connected = True
        self.server_waiting = False  # 接続されたので待機解除
        self._start_recv_thread()


    def connect_to_server(self, ip, port=5000):
        client = socket.socket()
        try:
            client.connect((ip, port))
            self.conn = client
            self.connected = True
            self._start_recv_thread()
        except Exception as e:
            print("接続失敗:", e)

    def _start_recv_thread(self):
        self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.recv_thread.start()

    def _recv_loop(self):
        while self.connected:
            try:
                data = self.conn.recv(1024)
                if not data:
                    print("接続が切断されました")
                    self.connected = False
                    break
                message = data.decode()
                with self.lock:
                    self.recv_buffer.append(message)
            except Exception as e:
                print("受信エラー:", e)
                self.connected = False
                break

    def send(self, data: str):
        if self.connected:
            try:
                self.conn.sendall(data.encode())
            except Exception as e:
                print("送信エラー:", e)
                self.connected = False

    def receive(self) -> str:
        with self.lock:
            if self.recv_buffer:
                return self.recv_buffer.pop(0)
        return None
    
    def get_my_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "IP取得失敗"
