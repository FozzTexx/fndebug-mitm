#!/usr/bin/env python3
import socket
import select
import sys
import binascii

LISTEN_PORT   = 65504
TARGET_HOST   = 'localhost'
TARGET_PORT   = 65504
BUFFER_SIZE   = 4096

def hexdump(prefix, data):
  # data is bytes; hexlify gives b'616263'
  hexdata = binascii.hexlify(data).decode('ascii')
  # group into pairs
  grouped = ' '.join(hexdata[i:i+2] for i in range(0, len(hexdata), 2))
  print(f"{prefix} {grouped}")

def main():
  # 1. listen
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  #server.bind(('0.0.0.0', LISTEN_PORT))
  server.bind(('10.4.0.242', LISTEN_PORT))
  server.listen(1)
  print(f"Listening on port {LISTEN_PORT}...")

  client_sock, client_addr = server.accept()
  print(f"Client connected from {client_addr}")

  # 2. connect to target
  remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  remote_sock.connect((TARGET_HOST, TARGET_PORT))
  print(f"Connected to {TARGET_HOST}:{TARGET_PORT}")

  sockets = [client_sock, remote_sock]

  while True:
    readable, _, _ = select.select(sockets, [], [])
    for s in readable:
      data = s.recv(BUFFER_SIZE)
      if not data:
        print("Connection closed.")
        client_sock.close()
        remote_sock.close()
        return

      if s is client_sock:
        hexdump("--> REMOTE:", data)
        remote_sock.sendall(data)
      else:
        hexdump("<-- REMOTE:", data)
        client_sock.sendall(data)

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    print("Exiting.")
