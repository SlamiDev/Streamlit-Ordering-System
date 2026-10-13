# < Modules >
from math import ceil
import streamlit as st
import yaml
import zmq
import time
from datetime import datetime
from pathlib import Path

st.cache_resource.clear()

parentDirectory = current_dir = Path(__file__).resolve().parent

# < Configs >
configPath = parentDirectory / "ClientConfig.yaml"
config = yaml.load(open(configPath, "r", encoding="utf-8"), Loader=yaml.FullLoader)
Client_Data = config["Client Data"]
Column_Count = Client_Data["Columns"]
Color_Limits = Client_Data["Color Limits"]
Order_Place_Debounce = Client_Data["OrderPlaceDebounce"]
Dish_Data = config["Dish Data"]
Menu = config["Menu"]
Shared_Data = config["Shared Data"]
Protocol = Shared_Data["RequestProtocol"]
Port = str(Shared_Data["RequestPort"])

# < Set up Page >
st.set_page_config(layout="wide", page_title="Order", page_icon=":material/point_of_sale:",)
st.title("Order")

# < Create ZMQ Socket >
@st.cache_resource(scope="session")
def createClientOrderSocket():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"{Protocol}://127.0.0.1:{Port}")
    return socket

socket = createClientOrderSocket()

if not "Cart" in st.session_state:
    st.session_state["Cart"] = {}

if not "CartDebounce" in st.session_state:
    st.session_state["CartDebounce"] = round(datetime.now().timestamp())

if "OrderNum" in st.session_state:
    st.toast(f"Order placed successfully as order {st.session_state["OrderNum"]}. Please wait at the counter.", icon=":material/check:", duration=5)
    st.session_state.pop("OrderNum")

tabs = []

# < Attempt to send an order >
def addOrder():
    newCart = {}
    for cartName in st.session_state["Cart"]:
        newCart[cartName] = st.session_state["Cart"][cartName]["Amount"]

    socket.send(str(newCart).encode('utf-8'))
    response = socket.recv().decode("utf-8")

    if response == "full":
        st.toast("The order list is full, please try again later or contact a member of staff", icon=":material/warning:", duration=4)
    elif response == "error":
        st.toast("An undiagnosable error has occured, please try again later or contact a member of staff", icon=":material/error:", duration=4)
    elif response.isnumeric():
        st.session_state["OrderNum"] = response
        st.session_state["Cart"] = {}
        st.rerun()

    st.session_state["CartDebounce"] = round(datetime.now().timestamp())

# < Add something to the cart >
def addCartItem(cartItem):
    if cartItem["Name"] in st.session_state["Cart"]:
         st.session_state["Cart"][cartItem["Name"]]["Amount"] += 1
    else:
         st.session_state["Cart"][cartItem["Name"]] = {
            "Amount":1,
            "Price":cartItem["Price"]
         }

# < Create whitespace >
def whitespace(page, count):
    for i in range(count):
        page.write("")

# < Create the cart UI >
def createCart(cartTab):
    cartTab.header("🛒 Cart", divider=True)
    totalCost = 0

    for cartName in st.session_state["Cart"]:
        cartData = st.session_state["Cart"][cartName]
        itemContainer = cartTab.container(border=True)
        itemContainer.subheader(cartName, divider=True)
        cost = (cartData["Price"] * cartData["Amount"])
        with itemContainer.container(horizontal=True): # [Edit the cart details]
            st.badge(str(cartData["Amount"]) + "x", color="blue")
            st.badge(Client_Data["Currency"] + str(round(cost, 2)), color="green")
        totalCost += cost

        with itemContainer.container(horizontal=True): # [Edit the cart details]
            if st.button("Add 1x to cart", type="primary", icon=":material/add_shopping_cart:", key="CartAdd" + cartName):
                st.session_state["Cart"][cartName]["Amount"] += 1

                st.rerun()

            st.space("small")

            if st.button("Remove 1x from cart", type="secondary", icon=":material/remove_shopping_cart:", key="CartRemove" + cartName):
                st.session_state["Cart"][cartName]["Amount"] -= 1
                if st.session_state["Cart"][cartName]["Amount"] <= 0:
                    st.session_state["Cart"].pop(cartName)

                st.rerun()
    
    if len(st.session_state["Cart"]) <= 0:
        cartTab.write("***Alone, at the edge of a universe humming a tune.***")
        cartTab.write("***For merely dreaming we were snow, mmh-mmh***")
        whitespace(cartTab, 5)
        cartTab.write("***A siren sounds like the goddess***")
        cartTab.write("***Who promises endless apologies of paradise***")
        cartTab.write("***And only she can make it right***")
        cartTab.write("***So things are different tonight***")
        cartTab.write("***We'll go together in flight***")
        cartTab.write("***It's now and never***")
    else:
        whitespace(cartTab, 2)
        cartTab.badge(f"Total Price: {Client_Data["Currency"]}{str(round(totalCost, 2))}", color="green")
        whitespace(cartTab, 1)
        with cartTab.container(horizontal=True): # [List the cart items and create the clear all and create order buttons]
            if st.button("Purchase", type="primary", icon=":material/attach_money:", key="CartPurchase"):
                if (datetime.now().timestamp() - st.session_state["CartDebounce"]) >= Order_Place_Debounce:
                    addOrder()
                else:
                    st.toast("Slow down!", icon=":material/bolt_boost:", duration=(datetime.now().timestamp() - st.session_state["CartDebounce"]))

            st.space("small")

            if st.button("Clear Cart", type="secondary", icon=":material/clear_all:", key="CartClear"):
                st.session_state["Cart"] = {}
                st.rerun()

# < Gather the nutrition data and color code it >
def gatherNutritionData(val, key):
    valData = Color_Limits[key]
    color = ""

    if val > valData["Min"] and val < valData["Max"]:
        color = "yellow"
    elif not valData["Reverse"]:
        if val < valData["Min"]:
            color = "green"
        else:
            color = "red"
    else:
        if val < valData["Min"]:
            color = "red"
        else:
            color = "green"

    return color, valData["Icon"], valData["Unit"]

# < Get the item from a dictionary at an index, essentially giving a dictionary list functionality >
def dictFromIndex(dictObj, index):
    count = 0
    for data in dictObj:
        if count >= index:
            return data, dictObj[data]
        count += 1

# < Create item in Menu for sale >
def createMenuItem(tabData, itemIndex, column):
    prodName, prodPrice = dictFromIndex(tabData, itemIndex)
    container = column.container(border=True)

    mainL, mainR = container.columns(2)
    mainL.title(prodName)

    mainL.badge(Client_Data["Currency"] + str(prodPrice), color="green")
    ll = mainL.columns(3)[1]

    if container.button("Add to cart", type="primary", icon=":material/add_shopping_cart:", key=prodName):
        st.toast(prodName + " has been added to cart!", icon=":material/check:")
        addCartItem({"Name":prodName, "Price":prodPrice})

    mainR.subheader("Nutrition :material/nutrition:", divider=True)
    rl, rr = mainR.columns(2)

    dishItems = Dish_Data[prodName]
    for category in dishItems:
        if category != "Ingredients":
            color, icon, unit = gatherNutritionData(dishItems[category], category)

            rl.badge(str(dishItems[category]) + unit, icon=":" + icon + ":", color=color)

    ingredients = rr.expander("Ingredients", icon=":material/menu_book:")
    ingredients.markdown(dishItems["Ingredients"])

# < Create all tabs for ordering based on the client config >
def createTabs():
    menu = []
    for menuItem in Menu:
        menu.append(menuItem)
    menu.append("🛒 Cart")

    global tabs
    tabs = st.tabs(menu)
    tabCount = 0

    for tab in tabs:
        if tabCount > len(Menu) - 1:
            createCart(tab)
            continue
        tabData = Menu[menu[tabCount]]

        columnIteration = ceil(len(tabData) / Column_Count)
        itemIndex = 0
        for columnIndex in range(columnIteration):
            columns = tab.columns(Column_Count)

            for column in columns:
                createMenuItem(tabData, itemIndex, column)

                itemIndex += 1

                if itemIndex >= len(tabData):
                    break

        tabCount += 1

createTabs()