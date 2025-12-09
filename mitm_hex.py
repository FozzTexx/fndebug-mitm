#!/usr/bin/env python3
import argparse
import os, sys
import socket
import select
import binascii
import serial
import pty
from hexdump import hexdump

BUFFER_SIZE   = 4096

def build_argparser():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("source", help="source host:addr or serial port")
  parser.add_argument("dest", nargs="?", help="dest host:addr")
  parser.add_argument("--flag", action="store_true", help="flag to do something")
  return parser

class ManInTheMiddle:
  def __init__(self, source, dest):
    if dest is None:
      self.initPTY(source)
      return

    self.initSocket(source, dest)
    return

  def initPTY(self, source):
    self.sourceFD = serial.Serial(source)
    parent_pty, child_pty = pty.openpty()
    child_name = os.ttyname(child_pty)
    print(f"Test should open this device as serial port: {child_name}", file=sys.stderr)
    self.destFD = parent_pty
    return

  def initSocket(self, source, dest):
    host, port = source.split(":")
    if host == "*":
      host = "0.0.0.0"
    port = int(port)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(1)
    print(f"Listening on {host}:{port}...")

    client_sock, client_addr = server.accept()
    print(f"Client connected from {client_addr}")

    host, port = dest.split(":")
    port = int(port)
    remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_sock.connect((host, port))
    print(f"Connected to {host}:{port}")

    self.sourceFD = client_sock
    self.destFD = remote_sock
    return

  def read(self, fd, length):
    if not isinstance(fd, int):
      fd = fd.fileno()
    return os.read(fd, length)

  def write(self, fd, data):
    if not isinstance(fd, int):
      fd = fd.fileno()
    return os.write(fd, data)

  def printData(self, fd, data):
    prefix = "MSX --> " if fd is self.sourceFD else "<-- FujiNet "
    hexdump(data, prefix=prefix)
    return
        
  def loop(self):
    ioPorts = [self.sourceFD, self.destFD]
    timeout = None
    lastFD = None
    accumData = bytes()
    while True:
      readable, _, _ = select.select(ioPorts, [], [], timeout)
      for fd in readable:
        data = self.read(fd, BUFFER_SIZE)
        if not data:
          print("Connection closed.")
          self.sourceFD.close()
          self.destFD_sock.close()
          return

        if accumData and fd is not lastFD:
          self.printData(lastFD, accumData)
          accumData = bytes()

        if fd is self.sourceFD:
          self.write(self.destFD, data)
        else:
          self.write(self.sourceFD, data)
          
        timeout = 0.5
        lastFD = fd
        accumData = accumData + data

      if not readable and accumData:
        self.printData(lastFD, accumData)
        accumData = bytes()
        
    return

def main():
  args = build_argparser().parse_args()
  mitm = ManInTheMiddle(args.source, args.dest)
  mitm.loop()
  return

if __name__ == "__main__":
  exit(main() or 0)
