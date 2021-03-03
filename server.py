import os
import socket
import sys
import _thread
import threading
import time
import re
import json

from config import *
from block import Block
from blockchain import Blockchain

server_sockets = []

# stores all operations not added to blockchain yet
queue = []
# stores key values
kv_store = {}
# blockchain contains dicts with operation, nonce, hash
blockchain = Blockchain()


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
        f.write("[")
        for i in range(len(blockchain.chain)):
            json.dump(blockchain.chain[i].to_dict(), f, indent=4)
            if (i < len(blockchain.chain) - 1):
                f.write(",")
        f.write("]")


def readFromFile():
    with open("blockchain.json", "r") as f:
        blocklist = json.load(f)
        print(blocklist)
        for block in blocklist:
            blockchain.append(Block(block["operation"], block["nonce"], block["hash"]))
            if(block["operation"][0] == "put"):
                kv_store[block["operation"][1]] = block["operation"][2]


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
    block1 = Block(("put", "key1", "val1"))
    block2 = Block(("put", "key2", "val2"))
    blockchain.append(block1)
    blockchain.append(block2)
    writeToFile()
    blockchain.clear()
    readFromFile()
    print(str(blockchain))
    print(kv_store)
    while True:
        conn, addr = server_socket.accept()
        print(addr)
        threading.Thread(target=handle_conn, args=(conn,)).start()
