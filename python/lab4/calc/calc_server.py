from math import factorial, sqrt
from socket import *
import threading


class ThreadedServer():
    def listenToClient(self, client, addr):
        print(addr, "logged in")
        while True:
            try:
                equation = client.recv(1024).decode()
                if equation == "exit!":
                    print(addr, "left the server")
                    client.send("exit!".encode())
                    break
                elif equation[len(equation) - 1] == "!":
                    try:
                        equation1 = int(equation[0:len(equation) - 1])
                        result = factorial(equation1)
                        print(addr, "typed:", equation)
                        client.send(str(result).encode())
                    except (ZeroDivisionError):
                        client.send("ZeroDiv".encode())
                    except (ArithmeticError):
                        client.send("MathError".encode())
                    except (SyntaxError):
                        client.send("SyntaxError".encode())
                    except (NameError):
                        client.send("NameError".encode())
                    except ValueError:
                        client.send("ValueError".encode())
                elif equation[0:4] == "sqrt":
                    try:
                        equation1 = int(equation[4:len(equation)])
                        print(equation1)
                        result = sqrt(equation1)
                        print(addr, "typed:", equation)
                        client.send(str(result).encode())
                    except (ZeroDivisionError):
                        client.send("ZeroDiv".encode())
                    except (ArithmeticError):
                        client.send("MathError".encode())
                    except (SyntaxError):
                        client.send("SyntaxError".encode())
                    except (NameError):
                        client.send("NameError".encode())
                    except ValueError:
                        client.send("ValueError".encode())
                else:
                    print(addr, "typed:", equation)
                    result = eval(equation)
                    client.send(str(result).encode())
            except (ZeroDivisionError):
                client.send("ZeroDiv".encode())
            except (ArithmeticError):
                client.send("MathError".encode())
            except (SyntaxError):
                client.send("SyntaxError".encode())
            except (NameError):
                client.send("NameError".encode())

        client.close()

    def __init__(self, serverPort):
        try:
            self.serverSocket = socket(AF_INET, SOCK_STREAM)
        except:
            print("Socket cannot be created!!!")
            exit(1)
        print("Socket is created...")
        try:
            self.serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        except:
            print("Socket cannot be used!!!")
            exit(1)
        print("Socket is being used...")
        try:
            self.serverSocket.bind(('', serverPort))
        except:
            print("Binding cannot de done!!!")
            exit(1)
        print("Binding is done...")
        try:
            self.serverSocket.listen(1)
        except:
            print("Server cannot listen!!!")
            exit(1)
        print("The server is ready to receive")
        while True:
            connectionSocket, addr = self.serverSocket.accept()
            threading.Thread(target=self.listenToClient, args=(connectionSocket, addr)).start()


if __name__ == "__main__":
    serverPort = 5005
    ThreadedServer(serverPort)
