"""
This is the simple Python TCP port scanner.
To be used for basic troubleshooting of connectivity/firewall/port forwarding issues, where
the tools like nmap are not available.
"""

import socket
import threading
import queue

connection_timeout = 1
start_port = 1
end_port = 65535
targets = ["192.168.1.1"]  # hosts or IPs
num_threads = 64

lock = threading.Lock()

def worker():
      while not q.empty():
            target, port = q.get()
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                socket.setdefaulttimeout(connection_timeout)
                result = s.connect_ex((target,port))
                if result == 0:
                    try:
                        portname = socket.getservbyport(port, "tcp")
                    except OSError:
                         portname = "?"
                    with lock:
                        print(f"{target}: Port {port} is open ({portname})")

q = queue.Queue()
for target in targets:
    # check if host name is ok:
    addr = socket.gethostbyname(target)
    for port in range(start_port, end_port + 1):
        q.put((target, port))

threads = []
for _ in range(min(num_threads, q.qsize())):
    t = threading.Thread(target=worker, daemon=False)
    t.start()
    threads.append(t)

for t in threads:
    t.join()
print('Scan finished')
