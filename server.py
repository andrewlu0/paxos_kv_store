import os
import socket
import sys
import _thread
import threading
import time
import re
import json
import pickle

from config import *
from block import Block, Operation
from blockchain import Blockchain
from hashlib import sha256
from random import randint
from ast import literal_eval as make_tuple

mutex = threading.Lock()
monitor = threading.Condition()
seq_num = 0

server_sockets = {}

# stores all operations not added to blockchain yet
queue = []
# stores key values
kv_store = {}
# blockchain contains dicts with operation, nonce, hash
blockchain = Blockchain()
# simulates failed link between src (current process) and process in set
failed_links = set()
# leader
leader = None

ballot_num = list()
accept_num = [-1, -1, -1]
accept_val = Block()

majority_accept = threading.Event()

DELAY = 2

def writeToFile(pid):
    with open("blockchain_{}.json".format(pid), "w") as f:
        arr = []
        for block in blockchain.chain:
            print(block.operation)
            arr.append(block.to_dict())
        json.dump(arr, f, indent=4)

def readFromFile(pid):
    with open("blockchain_{}.json".format(pid), "r") as f:
        blocklist = json.load(f)
        
        for block in blocklist:
            operation = Operation(block["operation"]["op"],block["operation"]["key"],block["operation"]["value"])
            blockchain.append(Block(operation, block["nonce"], block["hash"]))
            
            if(block["operation"]["op"] == "put"):
                kv_store[block["operation"]["key"]] = dict(block["operation"]["value"])

def get_hash(prev_block):
    """get hash pointer based on contents of previous block"""
    if not prev_block:
        return None
    hash = sha256((str(prev_block.operation) + str(prev_block.nonce) + str(prev_block.hash)).encode())
    return hash.hexdigest()

def get_nonce(operation):
    """find nonce where last character in sha256 concatenated string is between 0 and 2"""
    nonce = ""
    result = "-1"
    while True:
        nonce = randint(0, 1000)
        result = sha256((str(operation) + str(nonce)).encode()).hexdigest()
        if result[-1] in ["0", "1", "2"]:
            return nonce

def close_connections():
    for processID in server_sockets:
        server_sockets[processID].close()
        # connection[0].close()
    os._exit(0)

def open_connections():
    for i in range(5):
        if i != pid:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((IP, pid_ports[i]))
            server_sockets[i] = conn
            #server_sockets.append((conn, i))

def handle_input():
    while True:
        user_input = input()
        if user_input == "c":
            open_connections()
        elif user_input == "exit":
            close_connections()
        # failLink
        elif user_input.split(' ')[0] == "faill":
            print("Failing link to " + user_input.split(' ')[1])
            failed_links.add(int(user_input.split(' ')[1]))
        # fixLink
        elif user_input.split(' ')[0] == "fixl":
            print("Fixing link to " + user_input.split(' ')[1])
            if int(user_input.split(' ')[1]) in failed_links:
                failed_links.remove(int(user_input.split(' ')[1]))
        # failProcess
        elif user_input == "fp":
            writeToFile(pid)
            close_connections()
        # printBlockchain
        elif user_input == "pb":
            print(blockchain)
        # printKVStore
        elif user_input == "pkv":
            print(kv_store)
        # printQueue
        elif user_input == "pq":
            print(queue)
        else:
            # TODO
            # print("Sending message: ", user_input)
            # for processID in server_sockets:
            #     server_sockets[processID].sendall(user_input.encode())
            pass

def process_queue():
    while True:
        # wait for non-empty queue
        with monitor:
            monitor.wait_for(lambda: queue)
        operation = queue[0]
        nonce = get_nonce(queue[0])
        hash = get_hash(blockchain.last())
        new_block = Block(operation, nonce, hash)
        # max_ballot = promises[0][2]
        # max_val = promises[0][3]
        # all_vals_null = True

        # for promise in promises:
        #     if tuple(promise[2]) > tuple(max_ballot):
        #         max_ballot = promise[2]
        #         max_val = promise[3]
        #     if not promise[3].is_empty():
        #         all_vals_null = False
        
        # my_val = new_block if all_vals_null else max_val
        msg = ["accept",ballot_num,new_block]
        accepts = []
        time.sleep(DELAY)
        for processID in server_sockets:
            if processID not in failed_links:
                try:
                    server_sockets[processID].sendall(pickle.dumps(msg))
                except:
                    pass
        for processID in server_sockets:
            if processID not in failed_links:
                data = b""
                while True:
                    try:
                        packet = server_sockets[processID].recv(4096)
                        data += packet
                        if len(packet) < 4096:
                            break
                    except:
                        pass
                if not data:
                    continue
                data = pickle.loads(data)
                print(data)
                accepts.append(data)
        if (len(accepts) > 1):
            blockchain.append(new_block)
            majority_accept.set()
            queue.pop(0)
            msg = ["decide",ballot_num,new_block]
            time.sleep(DELAY)
            for processID in server_sockets:
                if processID not in failed_links:
                    try:
                        server_sockets[processID].sendall(pickle.dumps(msg))
                    except:
                        pass
        else:
            queue.pop(0)
           
def elect_leader():
    print("elect leader")
    with mutex:
        ballot_num[1] += 1
        ballot_num[2] = pid
    promises = []
    time.sleep(DELAY)
    for processID in server_sockets:
        if processID not in failed_links:
            msg = ["prepare", ballot_num]
            try:
                server_sockets[processID].sendall(pickle.dumps(msg))
            except:
                pass
    for processID in server_sockets:
        if processID not in failed_links:
            data = b""
            while True:
                try:
                    packet = server_sockets[processID].recv(4096)
                    data += packet
                    if len(packet) < 4096:
                        break
                except:
                    pass
            if not data:
                continue
            data = pickle.loads(data)
            print(data)
            promises.append(data)

    # check majority vote
    if (len(promises) < 2):
        return False

    threading.Thread(target = process_queue).start()
    return True

def handle_conn(conn):
    global leader
    while True:
        data = b""
        while True:
            try:
                packet = conn.recv(4096)
                data += packet
                if len(packet) < 4096:
                    break
            except:
                pass
        
        if not data:
            break

        encoded = data
        data = pickle.loads(data)
    
        print("received msg: " + str(data))
        print("leader is " + str(leader))
        if data == "Leader":
            leader = pid
            # execute leader election
            if elect_leader():
                time.sleep(DELAY)
                conn.sendall("ack".encode())     
        # Operation
        elif isinstance(data, str) and data.split(' ')[0] == "Operation":
            if leader != pid:
                time.sleep(DELAY)
                print("sending to leader")
                try:
                    server_sockets[leader].sendall(encoded)
                except:
                    continue
                res = server_sockets[leader].recv(1024)
                time.sleep(DELAY)
                conn.sendall(res)
                return
            op = data.split(' ')[1]
            netid = data.split(' ')[2]
            try:
                phone = {"phone":data.split(' ')[3]}
            except:
                phone = None
            if op == "get":
                with mutex:
                    queue.append(Operation(op, netid, phone))
                with monitor:
                    monitor.notify_all()
                majority_accept_set = majority_accept.wait()
                if majority_accept_set:
                    time.sleep(DELAY)
                    if netid in kv_store:
                        conn.sendall(str(kv_store[netid]).encode())
                    else:
                        conn.sendall("NO_KEY".encode())
                    majority_accept.clear()
            elif op == "put":
                with mutex:
                    queue.append(Operation(op, netid, phone))
                with monitor:
                    monitor.notify_all()
                majority_accept_set = majority_accept.wait()
                if majority_accept_set:
                    kv_store[netid] = phone
                    time.sleep(DELAY)
                    conn.sendall("ack".encode())
                    majority_accept.clear()
        else:
            global ballot_num, accept_num, accept_val
            if data[0] == "prepare":
                print("Received prepare message")
                recv_ball_num = tuple(data[1])
                if recv_ball_num >= tuple(ballot_num):
                    ballot_num = data[1]
                    # global leader
                    leader = ballot_num[2]
                    msg = ["promise", ballot_num, accept_num, accept_val]
                    time.sleep(DELAY)
                    conn.sendall(pickle.dumps(msg))
            elif data[0] == "accept":
                recv_ball_num = tuple(data[1])
                if recv_ball_num >= tuple(ballot_num):
                    accept_num = data[1]
                    accept_val = data[2]
                    msg = ["accepted", data[1], data[2]]
                    time.sleep(DELAY)
                    conn.sendall(pickle.dumps(msg))
            elif data[0] == "decide":
                blockchain.append(data[2])
                if data[2].operation.op == "put":
                    kv_store[data[2].operation.key] = data[2].operation.value


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
    try:
        readFromFile(pid)
    except Exception as e:
        print(e)
    # print(str(blockchain))
    print(kv_store)
    # ballot num
    ballot_num = [len(blockchain.chain), 0, pid]
    # elect_leader()
    while True:
        conn, addr = server_socket.accept()
        print(addr)
        threading.Thread(target=handle_conn, args=(conn,)).start()
