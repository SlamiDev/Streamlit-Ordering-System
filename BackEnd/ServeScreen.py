# < Modules >
import streamlit as st
import yaml
from datetime import datetime
from math import ceil
from ast import literal_eval as toDict
import os
from pathlib import Path

st.cache_resource.clear()

parentDirectory = current_dir = Path(__file__).resolve().parent
ancestorDirectory = parentDirectory.parent

# < Configs >
clientConfigPath = ancestorDirectory / "FrontEnd" / "ClientConfig.yaml"
serverConfigPath = parentDirectory / "ServerConfig.yaml"
clientConfig = yaml.load(open(clientConfigPath, "r", encoding="utf-8"), Loader=yaml.FullLoader)
serverConfig = yaml.load(open(serverConfigPath, "r", encoding="utf-8"), Loader=yaml.FullLoader)
Order_Directory = serverConfig["OrderDirectory"]
OrderTimeThresholds = serverConfig["OrderTimeThresholds"]
Order_Complete_Tag = clientConfig["Shared Data"]["OrderCompletionTag"]

# < Create Page >
st.set_page_config(layout="wide", page_title="Serve", page_icon=":material/point_of_sale:",)
st.title("Orders to serve")

# < Gather order time color based on time active >
def gatherOrderTimeColor(time):
    lastColor = ""
    longest = 0

    for timeSection in OrderTimeThresholds:
        if int(OrderTimeThresholds[timeSection]["Threshold"]) >= longest:
            longest = OrderTimeThresholds[timeSection]["Threshold"]
            lastColor = OrderTimeThresholds[timeSection]["Color"]
        if time <= int(OrderTimeThresholds[timeSection]["Threshold"]):
            return OrderTimeThresholds[timeSection]["Color"].lower()
    return lastColor.lower()

# < Add commas every 3rd digit >
def getComma(number):
    string = ""
    count = 0
    for letter in range(len(number) - 1, -1, -1):

        string = number[letter] + string

        count += 1
        if count >= 3 and 1 <= letter:
            string = f", {string}"
            count = 0
    return string

# < Create and update the server UI, contains each order and what needs to be made >
@st.fragment(run_every=1)
def createServerUI():
    columns = st.columns(3)
    activeOrders = os.listdir(Order_Directory)
    
    count = 0
    if len(activeOrders) <= 0:
        st.header("No orders to serve, chillax for a bit.", divider=True)
    for activeOrder in activeOrders:
        if activeOrder.find(Order_Complete_Tag) != -1:
            continue
        fileName = f"{Order_Directory}/{activeOrder}"
        orderFile = open(fileName, "r")
        orderFileText = orderFile.read()
        orderFile.close()
        orderDetails = toDict(orderFileText)
        column = columns[count % 3]

        details = column.expander(activeOrder, expanded=True, icon=":material/receipt_long:")

        for item in orderDetails:
            if item == "Time":
                continue
            smallCont = details.container()
            smallCont.subheader(item + ": " + str(orderDetails[item]) + "x")
        
        
        timeHad = ceil(datetime.now().timestamp()) - orderDetails["Time"]
        details.badge("Time Since Ordered: " + getComma(str(timeHad)), icon=":material/hourglass:", color=gatherOrderTimeColor(timeHad))
        
        buttonContainer = details.container(horizontal=True)

        if buttonContainer.button("Complete Order", type="secondary", icon=":material/delete:", key="OrderComplete" + activeOrder + item):
            if os.path.isfile(fileName):
                os.rename(fileName, fileName + Order_Complete_Tag)

        if buttonContainer.button("Cancel Order", type="primary", icon=":material/delete:", key="OrderRemove" + activeOrder + item):
            if os.path.isfile(fileName):
                os.remove(fileName)

        count += 1

    

createServerUI()