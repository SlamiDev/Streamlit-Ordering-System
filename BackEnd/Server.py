# < Modules >

import yaml
import zmq
from time import sleep as wait
from os import listdir as listFiles
from os import remove as deleteFile
from datetime import datetime
from math import log10, ceil
from ast import literal_eval as toDict
from multiprocessing import Process
from pathlib import Path

parentDirectory = current_dir = Path(__file__).resolve().parent
ancestorDirectory = parentDirectory.parent

# < Configs >
clientConfigPath = ancestorDirectory / "FrontEnd" / "ClientConfig.yaml"
serverConfigPath = parentDirectory / "ServerConfig.yaml"
clientConfig = yaml.load(open(clientConfigPath, "r", encoding="utf-8"), Loader=yaml.FullLoader)
serverConfig = yaml.load(open(serverConfigPath, "r", encoding="utf-8"), Loader=yaml.FullLoader)
Shared_Data = clientConfig["Shared Data"]
Order_Digits = Shared_Data["OrderDigits"]
Order_Protocol = Shared_Data["RequestProtocol"]
Order_Port = str(Shared_Data["RequestPort"])
Progress_Protocol = Shared_Data["OrdersRequestProtocol"]
Progress_Port = str(Shared_Data["OrdersRequestPort"])
Login_Protocol = serverConfig["LoginProtocol"]
Login_Port = str(serverConfig["LoginPort"])
Create_Login_Protocol = serverConfig["CreateLoginProtocol"]
Create_Login_Port = str(serverConfig["CreateLoginPort"])
Order_Directory = serverConfig["OrderDirectory"]
Login_Directory = serverConfig["LoginDirectory"]
Manager_API_Key = serverConfig["ManagerKey"]
Order_Complete_Tag = Shared_Data["OrderCompletionTag"]
File_Expiry_Time = serverConfig["FileExpiryTime"]

# < ZMQ Sockets >
context = zmq.Context.instance()

def createServerOrderSocket():
    sock = context.socket(zmq.REP)
    sock.bind(f"{Order_Protocol}://127.0.0.1:{Order_Port}")
    return sock

def createServerProgressSocket():
    sock = context.socket(zmq.REP)
    sock.bind(f"{Progress_Protocol}://127.0.0.1:{Progress_Port}")
    return sock

def createLoginSocket():
    sock = context.socket(zmq.REP)
    sock.bind(f"{Login_Protocol}://127.0.0.1:{Login_Port}")
    return sock

def createCreateLoginSocket():
    sock = context.socket(zmq.REP)
    sock.bind(f"{Create_Login_Protocol}://127.0.0.1:{Create_Login_Port}")
    return sock

orderCount = 0

# < Create order string and add zeros to elongate it so it remains the same digits >
def getOrderString():
    global orderCount

    if orderCount == 0:
        return "0" * Order_Digits

    placeholders = "0" * (Order_Digits - max(1, ceil(log10(orderCount))))
    return placeholders + str(orderCount)

# < Create an order by writing it into a file >
def createOrder(orderDetails, iterations):
    global orderCount

    try:
        newOrderFile = open(f"{Order_Directory}/Order{getOrderString()}.txt", "x")
        newOrderFile.write(orderDetails)
        newOrderFile.close()
        return getOrderString()
    except:
        orderCount += 1 # Slightly inefficient but it helps incase an order isn't completed yet.
        if orderCount // (10**Order_Digits) >= 1:
            orderCount = 0
        return createOrder(orderDetails, iterations + 1)

# < ZMQ Socket Thread for Creating Orders >
def createOrderThread():
    socket = createServerOrderSocket()
    
    while True:
        data = socket.recv().decode("utf-8")
    
        try:
            orderDetails = toDict(data)
            orderDetails["Time"] = ceil(datetime.now().timestamp())

            answer = createOrder(str(orderDetails), 0)
            if answer:
                socket.send(getOrderString().encode("utf-8"))
            else:
                socket.send(b"full")
        except:
            socket.send(b"error")

# < ZMQ Socket Thread for Sending Orders to Progression Screen >
def sendProgressThread():
    socket = createServerProgressSocket()

    while True:
        data = socket.recv()
        socket.send(str(listFiles(Order_Directory)).encode("utf-8"))

# < ZMQ Socket Thread for the Login Requests for Managers >
def managerLoginThread():
    socket = createLoginSocket()

    while True:
        data = socket.recv().decode("utf-8")

        sections = data.split("/")

        if len(sections) != 2:
            socket.send(b"Error")
            continue

        username = sections[0]
        password = sections[1]

        loginsFile = open(Login_Directory, "r")
        fileData = loginsFile.read()
        loginsFile.close()

        dataSplit = fileData.split("%")
        for dataSection in dataSplit:
            if dataSection == data:
                socket.send(Manager_API_Key.encode("utf-8"))
                continue

        socket.send("NotFound".encode("utf-8"))

# < ZMQ Socket Thread for the Manager(s) Login >
def managerLoginCreateThread():
    socket = createCreateLoginSocket()

    while True:
        data = socket.recv().decode("utf-8")

        sections = data.split("/")

        if len(sections) != 2:
            socket.send("False".encode("utf-8"))
            continue

        username = sections[0]
        password = sections[1]

        loginsFile = open(Login_Directory, "a+")
        text = loginsFile.read()
        if text.find(username) != -1:
            socket.send("Same".encode("utf-8"))
            continue
        data = loginsFile.write(f"{data}%")
        loginsFile.close()
        socket.send("True".encode("utf-8"))
    

# < Check if it IS running by itself as well as creating all threads for sockets and checking if >
if __name__ == "__main__":
    createThread = Process(target=createOrderThread)
    sendThread = Process(target=sendProgressThread)
    loginThread = Process(target=managerLoginThread)
    loginCreateThread = Process(target=managerLoginCreateThread)

    createThread.start()
    sendThread.start()
    loginThread.start()
    loginCreateThread.start()

    while True:
        files = listFiles(Order_Directory)
        completedFiles = []

        for fileName in files:
            if fileName.find(Order_Complete_Tag) != -1:
                completedFiles.append(fileName)

        for file in completedFiles:
            fileOpen = open(f"{Order_Directory}/{file}", "r")
            fileText = fileOpen.read()
            fileOpen.close()
            dictionary = toDict(fileText)
            if (ceil(datetime.now().timestamp()) - dictionary["Time"]) >= File_Expiry_Time: # [Remove files when they last too long]
                deleteFile(f"{Order_Directory}/{file}")

        wait(10)

    