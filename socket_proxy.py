"""
This is the simple socket-level proxy server that does forwarding of all packets to another target server and back.
May be used to:
- create a simple non-tls reverse proxy to another server
- downgrade TLS connection to non-tls one
- provide downgraded connection to TLS-only server, that is usable by old devices that do not support secure connections, or are no longer updated and have expired certificates
- sniff protocols like HTTP, SMTP, IMAP, FTP and so on
"""

import socket
import threading
import ssl

LISTEN_ADDRESS = ''  # typically listen on any interface on the server. "127.0.0.1" will only accept connections on the same computer.
LISTEN_PORT = 88
TARGET_ADDRESS = "example.com"
TARGET_PORT = 443
TARGET_SSL = True
BUFFER_SIZE = 1024


def remoteHandler(conn, conn_to_local):
    while True:
        received = conn.recv(BUFFER_SIZE)
        print(f"Remote: {received}")
        if not received:
            conn.close()
            print("Closing remote thread")
            return
        # If using HTTP, it may be needed to do some string replacements, to make CORS working
        #received = received.replace(b"https://example.com", b"http://localhost:88")
        conn_to_local.send(received)


def handler(conn):
    with conn:
        with socket.socket() as s2:
            if TARGET_SSL:
                context = ssl.create_default_context()
                wrapped_socket = context.wrap_socket(s2, server_hostname=TARGET_ADDRESS)
            else:
                wrapped_socket = s2
            wrapped_socket.connect((TARGET_ADDRESS, TARGET_PORT))
            threading.Thread(target=remoteHandler, args=(wrapped_socket, conn)).start()
            while True:
                received = conn.recv(BUFFER_SIZE)
                if not received: break
                print(f"Local: {received}")
                # If using HTTP, it may be needed to do some string replacements, to make HOST and CORS working
                # received = received.replace(b"Host: localhost:88", b"Host: example.com")
                # received = received.replace(b"http://localhost:88", b"http://example.com")
                wrapped_socket.send(received)
            wrapped_socket.close()
            print("Closing client thread")


with socket.socket() as s:
    s.bind((LISTEN_ADDRESS, LISTEN_PORT))
    s.listen()

    while True:
        conn, addr = s.accept()
        print(f"Connected by {addr}")
        threading.Thread(target=handler, args=(conn,)).start()
