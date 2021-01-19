from socket import *
import datetime
import time
import threading


class ThreadedServer():

    def listenToClient(self, client, addr):
        userName = (client.recv(1024)).decode("utf-8")
        print(userName, "logged in")
        while True:
            counter = 0
            answers = []
            questions = []
            choice = (client.recv(1024)).decode("utf-8")
            if choice == "0":
                print(userName, "left the server")
                client.close()
                return
            else:
                if choice == "1":
                    testName = "Networks test"
                elif choice == "2":
                    testName = "Russian test"
                elif choice == "3":
                    testName = "Math test"
                print(userName, "started", testName)
                if choice == "1":
                    questions = self.questions1
                elif choice == "2":
                    questions = self.questions2
                else:
                    questions = self.questions3
                for i in range(6):
                    client.send(questions[counter].encode())
                    message = client.recv(1024)
                    if message == "exit":
                        print(addr, " is closed")
                        client.close()
                    else:
                        answers.append(message.decode("utf-8").upper())
                        ts = time.time()
                        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                        print(userName, "give answer", answers[counter], "for question", counter + 1,
                              "timestamp:",
                              st)
                        counter += 1
                self.assessment(addr, answers, userName, int(choice), client, testName)

    def assessment(self, addr, answers, userName, choice, client, testName):

        point = 0
        print(userName, "answers for", testName, answers)
        if choice == 1:
            if (answers[0] == "A"):
                point += 1
            if (answers[1] == "A"):
                point += 1
            if (answers[2] == "A"):
                point += 1
            if (answers[3] == "C"):
                point += 1
            if (answers[4] == "D"):
                point += 1
            if (answers[5] == "A"):
                point += 1
        elif choice == 2:
            if (answers[0] == "A"):
                point += 1
            if (answers[1] == "A"):
                point += 1
            if (answers[2] == "A"):
                point += 1
            if (answers[3] == "A"):
                point += 1
            if (answers[4] == "A"):
                point += 1
            if (answers[5] == "A"):
                point += 1
        elif choice == 3:
            if (answers[0] == "B"):
                point += 1
            if (answers[1] == "B"):
                point += 1
            if (answers[2] == "B"):
                point += 1
            if (answers[3] == "B"):
                point += 1
            if (answers[4] == "B"):
                point += 1
            if (answers[5] == "B"):
                point += 1
        if (point < 2):
            success_comment = "Mark is 2"
        elif (point < 4):
            success_comment = "Mark is 3"
        elif (point <= 5):
            success_comment = "Mark is 4"
        else:
            success_comment = "Mark is 5"

        client.send(("Your result of " + testName + " " + str(point) + "/6 | " + success_comment).encode())
        result = "Socket Information: " + str(addr[0]) + ":" + str(addr[1]) + " | Username: " + userName \
                 + " | Result:" + str(point) + "/6 | " + success_comment
        print(result)
        return result

    def __init__(self, serverPort):
        with open('questions.txt') as inp:
            self.sets = inp.read().split("FINISH")
            self.questions1 = self.sets[0].split("''',")
            self.questions2 = self.sets[1].split("''',")
            self.questions3 = self.sets[2].split("''',")
        self.answers = []
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
    serverPort = 5006
    ThreadedServer(serverPort)