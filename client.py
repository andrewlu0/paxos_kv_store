import os
import socket
import sys
import _thread
import threading
import time
import pickle

from config import *
from random import randint

received = False
received_list = []
conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
IP = socket.gethostname()
PORT = int(sys.argv[1])

def timeout(index, user_input):
    global conn, PORT
    print("timeout thread started")
    time.sleep(40)
    if not received_list[index]:
        # send leader to diff server
        print("TIMED OUT")
        old_leader = PORT
        PORT = pid_ports[randint(0,4)]
        while PORT == old_leader:
            PORT = pid_ports[randint(0,4)]
        print("Sending to new leader: " + str(PORT))
        conn.close()
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((IP, PORT))
        conn.sendall(pickle.dumps("Leader"))
        data = conn.recv(1024).decode()
        print(data)
        conn.sendall(pickle.dumps(user_input))
        data = conn.recv(1024).decode()
        print(data)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <PORT>")
        sys.exit()

    conn.connect((IP, PORT))

    index = 0

    while True:
        user_input = input()
        received_list.append(False)
        conn.sendall(pickle.dumps(user_input))
        threading.Thread(target = timeout, args = (index,user_input,)).start()
        try:
            data = conn.recv(1024).decode()
            received_list[index] = True
            print(data)
        except:
            print("Servers probably down")
        index += 1
