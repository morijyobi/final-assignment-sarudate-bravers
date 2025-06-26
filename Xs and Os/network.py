import socket
import threading

class Network:
    def __init__(self):
        self.conn = None
        self.connected = False

    def start_server(self, port=5000):
        server = socket.socket()
        server.bind(("0.0.0.0", port))
        server.listen(1)
        self.conn, addr = server.accept()
        print("クライアントが接続:", addr)
        self.connected = True

    def connect_to_server(self, ip, port=5000):
        client = socket.socket()
        try:
            client.connect((ip, port))
            self.conn = client
            self.connected = True
        except Exception as e:
            print("接続失敗:", e)

    def send(self, data: str):
        if self.connected:
            self.conn.send(data.encode())

    def receive(self) -> str:
        if self.connected:
            return self.conn.recv(1024).decode()
        return ""
    
    def get_my_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "IP取得失敗"
