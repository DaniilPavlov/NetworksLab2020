from socket import *

serverName = "localhost"
serverPort = 5005

clientSocket = socket(AF_INET, SOCK_STREAM)

clientSocket.connect((serverName, serverPort))

operation = {
    '+': 0,
    '-': 1,
    '*': 2,
    '/': 3,
}

print("The IP address of the server:", serverName, ", port: ", serverPort)

while (True):
    valid = False
    while not valid:
        print("Type your equation: arg |+,-,*,/| arg or arg! or sqrt|arg")
        print("Type exit! to quit")
        equ = input("Input line: ")
        if "!" not in equ and "sqrt" not in equ:
            line = equ.split(" ")
            if len(line) == 3:
                if line[1] in operation:
                    try:
                        arg1 = int(line[0])
                        arg3 = int(line[2])
                        valid = True
                        clientSocket.send((line[0] + line[1] + line[2]).encode())
                    except error:
                        print("wrong arguments")
                else:
                    print("wrong operation")
            else:
                print("wrong input. Example: 1 + 1 ; 2 * 2 ; 3 - 3 ; 4 / 4")
        else:
            valid = True
            clientSocket.send(equ.encode())


    try:
        result = clientSocket.recv(1024).decode()
    except ConnectionResetError:
        print(f'Closed connection')
        clientSocket.shutdown(socket.SHUT_RDWR)
        clientSocket.close()
        exit(0)

    if not result:
        print(f'Closed connection')
        clientSocket.shutdown(socket.SHUT_RDWR)
        clientSocket.close()
        exit(0)
    if result == "exit!":
        print("You left the server")
        clientSocket.close()
        exit(0)
    elif result == "ZeroDiv":
        print("You can't divide by 0, try again")
    elif result == "MathError":
        print("There is an error with your math, try again")
    elif result == "SyntaxError":
        print("There is a syntax error, please try again")
    elif result == "NameError":
        print("You did not enter an equation, try again")
    else:
        print("The answer is:", result)