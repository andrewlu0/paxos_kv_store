import os
import socket
import sys
import _thread
import threading
import time

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <PORT>")
        sys.exit()
    
    IP = socket.gethostname()
    PORT = int(sys.argv[1])

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((IP, PORT))

    while True:
        user_input = input()
        conn.sendall(user_input.encode())

