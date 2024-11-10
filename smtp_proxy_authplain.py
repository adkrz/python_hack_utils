"""
This proxy server translates commands from legacy SMTP client (that supports AUTH LOGIN + no TLS)
into a modern server (AUTH PLAIN + TLS)
"""

import socket
import threading
import ssl
import select
import base64

LISTEN_ADDRESS = ''  # typically listen on any interface on the server. "127.0.0.1" will only accept connections on the same computer.
LISTEN_PORT = 4466
TARGET_ADDRESS = "smtp.example.com"
TARGET_PORT = 465
TARGET_SSL = True
BUFFER_SIZE = 8192


def handler(conn):
    with conn:
        with socket.socket() as s2:
            if TARGET_SSL:
                context = ssl.create_default_context()
                wrapped_socket = context.wrap_socket(s2, server_hostname=TARGET_ADDRESS)
            else:
                wrapped_socket = s2
            wrapped_socket.connect((TARGET_ADDRESS, TARGET_PORT))

            conns = [conn, wrapped_socket]
            connected = True
            mode = ""
            username = ""
            try:
                while connected:
                    rlist, wlist, xlist = select.select(conns, [], conns, 2000)
                    if xlist or not rlist:
                        break
                    for r in rlist:
                        other = conns[1] if r is conns[0] else conns[0]
                        data = r.recv(BUFFER_SIZE)
                        if not data:
                            connected = False
                            break
                        print(data)
                        replaced = False
                        if r is conns[1]: # server
                            if data.startswith(b"250-"):
                                data = data.replace(b"PLAIN", b"PLAIN LOGIN")
                                replaced = True
                            elif data.startswith(b"334 "):
                                data = b"334 VXNlcm5hbWU6\r\n"
                                mode = "u"
                                replaced = True
                        else: # client
                            if data.startswith(b"AUTH LOGIN"):
                                data = b"AUTH PLAIN\r\n"
                                replaced = True
                            elif mode == "u":
                                username = base64.b64decode(data)
                                conns[0].sendall(b'334 UGFzc3dvcmQ6\r\n')
                                mode = "p"
                                continue
                            elif mode == "p":
                                password = base64.b64decode(data)
                                loginstr = b"\0" + username + b"\0" + password
                                print(b"Encoding: " + loginstr)
                                encoded = base64.b64encode(loginstr)
                                data = encoded + b"\r\n"
                                replaced = True
                                mode = ""
                        if replaced:
                            print(b"Replaced to: " + data)
                        other.sendall(data)
            except (ConnectionAbortedError, ConnectionResetError):
                conn.close()

            print("Closing client thread")


with socket.socket() as s:
    s.bind((LISTEN_ADDRESS, LISTEN_PORT))
    s.listen()

    while True:
        conn, addr = s.accept()

        print(f"Connected by {addr}")
        threading.Thread(target=handler, args=(conn,)).start()
