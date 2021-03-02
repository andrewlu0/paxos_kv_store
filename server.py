import os
import socket
import sys
import _thread
import threading
import time
import re
import json

from config import *

server_sockets = []

# stores all operations not added to blockchain yet
queue = []
# stores key values
dictionary = {}
# blockchain contains dicts with operation, nonce, hash
blockchain = []


def close_connections():
    for connection in server_sockets:
        connection.close()
    os._exit(0)


def open_connections():
    for i in range(5):
        if i != pid:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((IP, pid_ports[i]))
            server_sockets.append(conn)


def handle_input():
    while True:
        user_input = input()
        if user_input == "connect":
            open_connections()
        elif user_input == "exit":
            close_connections()
        else:
            print("Sending message: ", user_input)
            for conn in server_sockets:
                conn.sendall(user_input.encode())


def handle_conn(conn):
    while True:
        data = conn.recv(1024).decode()
        if not data:
            break
        print("Received message: ", data)


def writeToFile():
    with open("blockchain.json", "w") as f:
        json.dump(blockchain, f, indent=4)


def readFromFile():
    with open("blockchain.json", "r") as f:
        blockchain = json.load(f)
        print(blockchain)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <processID>")
        sys.exit()

    IP = socket.gethostname()
    pid = int(sys.argv[1])
    PORT = pid_ports[pid]
    print("Listening on " + str(IP) + ":" + str(PORT))
    server_socket = socket.socket()
    server_socket.bind((IP, PORT))
    server_socket.listen()
    input_thread = threading.Thread(target=handle_input)
    input_thread.start()
    block1 = {"operation": ("get", "key1", ""), "nonce": "nonce1", "hash": "hash1"}
    block2 = {"operation": ("put", "key2", "val2"), "nonce": "nonce2", "hash": "hash2"}
    blockchain.append(block1)
    blockchain.append(block2)
    writeToFile()
    blockchain = []
    readFromFile()
    while True:
        conn, addr = server_socket.accept()
        print(addr)
        threading.Thread(target=handle_conn, args=(conn,)).start()
