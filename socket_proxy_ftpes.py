"""
This is the simple socket-level proxy to do TLS downgrade on FTPES server.
FTPES protocol first negotiates TLS auth using plain text and then upgrades to secure connection.
Not to be confused with FTPS, that uses port 990 and initiates TLS from beginning.
A "normal" FTP is then exposed using LISTEN_PORT and can be used from old, incompatible device.
"""

import socket
import threading
import ssl

LISTEN_ADDRESS = ''  # typically listen on any interface on the server. "127.0.0.1" will only accept connections on the *same* computer.
LISTEN_PORT = 2222
TARGET_ADDRESS = "ftp.example.com"
TARGET_PORT = 21


def remoteHandler(conn_to_remote, conn_to_client):
    while True:
        received = conn_to_remote.recv(1024)
        print(f"Remote: {received}")
        if not received:
            conn_to_remote.close()
            print("Closing remote thread")
            return
        conn_to_client.send(received)


def handler(conn_to_client):
    with socket.socket() as s2:
        context = ssl.SSLContext(protocol=ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE  # my target had self-signed cert, otherwise create_default_context() is ok
        s2.connect((TARGET_ADDRESS, TARGET_PORT))
        welcome = s2.recv(1024)
        print(welcome)
        s2.send(b"AUTH TLS\r\n")
        r = s2.recv(1024)
        print(r)
        if not b"AUTH TLS OK" in r:
            raise Exception("Cannot use FTPES")
        wrapped_socket = context.wrap_socket(s2, server_hostname=TARGET_ADDRESS)

        threading.Thread(target=remoteHandler, args=(wrapped_socket, conn_to_client)).start()
        conn_to_client.send(welcome)
        try:
            while True:
                received = conn_to_client.recv(1024)
                if not received: break
                print(f"Local: {received}")
                wrapped_socket.send(received)
        except ConnectionResetError:
            pass  # Total Commander does not gracefully close connections :)
        wrapped_socket.close()
        print("Closing client thread")


with socket.socket() as s:
    s.bind((LISTEN_ADDRESS, LISTEN_PORT))
    s.listen()

    while True:
        conn_to_client, addr = s.accept()
        print(f"Connected by {addr}")
        threading.Thread(target=handler, args=(conn_to_client,)).start()
