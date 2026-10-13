# < Modules >
import streamlit as st
import yaml
import zmq
from pathlib import Path

st.cache_resource.clear()

parentDirectory = current_dir = Path(__file__).resolve().parent

# < Configs >
configPath = parentDirectory / "ClientConfig.yaml"
config = yaml.load(open(configPath, "r", encoding="utf-8"), Loader=yaml.FullLoader)
Client_Data = config["Client Data"]
Shared_Data = config["Shared Data"]
Protocol = Shared_Data["OrdersRequestProtocol"]
Port = str(Shared_Data["OrdersRequestPort"])
Order_Complete_Tag = Shared_Data["OrderCompletionTag"]
Order_Digits = Shared_Data["OrderDigits"]

# < Set up Page >
st.set_page_config(layout="wide", page_title="Progress", page_icon=":material/point_of_sale:",)

# < Create Socket >
@st.cache_resource(scope="session")
def createClientOrderSocket():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"{Protocol}://127.0.0.1:{Port}")
    return socket

socket = createClientOrderSocket()

container = st.empty()

# < Get order name from file, just the number >
def getOrderName(name):
    string = name.replace(Order_Complete_Tag, "")
    string = string.replace(".txt", "")
    return f"{string[0:len(string) - Order_Digits]} {string[len(string) - Order_Digits:len(string)]}"

# < Create progression UI >
@st.fragment(run_every=1)
def createUI():
    preparing, completed = container.columns(2)

    preparingCont = preparing.container(border=True)
    completedCont = completed.container(border=True)

    preparingCont.header("Preparing", divider="red")
    completedCont.header("Ready To Collect", divider="green")

    socket.send(b"")
    orders = socket.recv().decode("utf-8")
    print(orders)
    if len(orders) <= 0 or orders == "error" or orders == "[]":
        return
    orders = orders.replace("[", "")
    orders = orders.replace("]", "")
    orders = orders.replace("'", "")
    orders = orders.split(",")

    if orders:
        for orderName in orders:
            string = getOrderName(orderName)
            if orderName.find(Order_Complete_Tag) == -1:
                preparingCont.header(string)
            else:
                completedCont.header(string)

createUI()