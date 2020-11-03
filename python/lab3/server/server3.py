import socket
import time

sock = socket.socket()
host = input(str("Please enter the host address of the sender : "))
port = 5003
sock.connect((host, port))
print("Connected")

filename = input(str("Please enter a filename for the incoming file : "))
file = open(filename, 'wb')
file_data = sock.recv(1024)
file.write(file_data)
file.close()
print("File has been received successfully.")
time.sleep(3)
