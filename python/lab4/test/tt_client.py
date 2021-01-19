from socket import *

serverName = "localhost"
serverPort = 5006

clientSocket = socket(AF_INET, SOCK_STREAM)

clientSocket.connect((serverName, serverPort))


def main():
    user_main_menu()
    choice = make_choice_in_menu()
    if choice == 0:
        clientSocket.send(str(choice).encode())
        print("You left the server")
        clientSocket.close()
        exit(0)
    else:
        clientSocket.send(str(choice).encode())


def user_main_menu():
    print("\n"
          "====UNIVERSITY TEST SERVER====\n"
          "1 - Networks test\n"
          "2 - Russian test\n"
          "3 - Math test\n"
          "0 - Exit\n")


def make_choice_in_menu():
    while True:
        choice = input('Make a choice: ')
        try:
            if 0 <= int(choice) <= 3:
                return int(choice)
            else:
                print('Error. Your choice was out of range. Try again.\n')
        except ValueError:
            print('Error. You did not type number. Try again.')


msg = ""
while msg == "":
    msg = input('Please enter your name for authentication: ')
    if msg != "":
        clientSocket.send(msg.encode())
    else:
        print('Error. You did not type your name. Try again.')

while True:
    main()
    counter = 0
    for i in range(6):
        message = ""
        modifiedMessage = clientSocket.recv(1024)
        print('This is your question:', modifiedMessage.decode("utf-8"))
        while message == "":
            message = input('Your answer:')
            if message.upper() in ["A", "B", "C", "D"]:
                clientSocket.send(message.encode())
            else:
                print('Error. Your choice was out of range. Try again.\n')
                message = ""

        counter += 1
        if message == "exit":
            clientSocket.close()
            exit(0)
        else:
            print("Your answer was sent!")
    result_msg = clientSocket.recv(1024)
    print(result_msg.decode())
