import json
import socket


def send_temp(data):
    try:
        # Connect to the GUI's "ear" on port 5555
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", 5555))
            s.sendall(json.dumps(data).encode("utf-8"))
    except:
        pass  # GUI isn't listening, no big deal


def send_hash(data):
    try:
        # Connect to the GUI's "ear" on port 5555
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", 5556))
            s.sendall(json.dumps(data).encode("utf-8"))
    except:
        pass  # GUI isn't listening, no big deal
