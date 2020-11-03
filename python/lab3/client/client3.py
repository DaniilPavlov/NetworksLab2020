import socket
import time

sock = socket.socket()
host = socket.gethostname()
port = 5003
sock.bind((host, port))
sock.listen(1)
print(host)
print("Waiting for incoming connection")
conn, addr = sock.accept()
print(addr, "Has connected to the server")

filename = input(str("Please enter the filename of the transfer file: "))
file = open(filename , 'rb')
file_data = file.read(1024)
conn.send(file_data)
print("Data has been transmitted successfully.")
time.sleep(3)
