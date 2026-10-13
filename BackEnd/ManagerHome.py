# < Modules >
import streamlit as st
import yaml
import zmq
from random import randint
from datetime import datetime
from pathlib import Path

st.cache_resource.clear()

parentDirectory = current_dir = Path(__file__).resolve().parent

# < Configs >
serverConfigPath = parentDirectory / "ServerConfig.yaml"
serverConfig = yaml.load(open(serverConfigPath, "r", encoding="utf-8"), Loader=yaml.FullLoader)
Login_Debounce = serverConfig["LoginDebounce"]
Login_Protocol = serverConfig["LoginProtocol"]
Login_Port = str(serverConfig["LoginPort"])
settings = serverConfig["User Settings"]

# < Set up Page >
st.set_page_config(layout="wide", page_title="Overseer", page_icon=":material/point_of_sale:", initial_sidebar_state="expanded")

# < Create ZMQ Socket >
@st.cache_resource(scope="session")
def createLoginSocket():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"{Login_Protocol}://127.0.0.1:{Login_Port}")
    return socket

socket = createLoginSocket()

if not "LoginDebounce" in st.session_state:
    st.session_state["LoginDebounce"] = round(datetime.now().timestamp())

if not "ManagerAPIKey" in st.session_state:
    st.title("Login")
    with st.form("Login"):
        username = st.text_input("**Username:**", max_chars=settings["UsernameChars"], help="Cannot contain the symbol '/'!", key="Username", type="default", placeholder="Student123", icon=":material/badge:")
        password = st.text_input("**Password:**", max_chars=settings["PasswordChars"], help="Cannot contain the symbol '/'!", key="Password", type="password", placeholder="Password123", icon=":material/passkey:")

        if st.form_submit_button("Login", type="primary", icon=":material/check:", icon_position="left"):
            if (round(datetime.now().timestamp()) - st.session_state["LoginDebounce"]) >= Login_Debounce:
                socket.send(f"{username}/{password}".encode("utf-8"))
                response = socket.recv().decode("utf-8")
                if response == "Error":
                    st.toast(f"Unable to create login, please try again later and not use the symbols '/' or '%'!", icon=":material/error:", duration=5)
                elif response == "NotFound":
                    st.toast(f"Invalid username or password!", icon=":material/warning:", duration=5)
                else:
                    st.session_state["ManagerAPIKey"] = response
                    st.rerun()
                st.session_state["LoginDebounce"] = round(datetime.now().timestamp())
            else:
                st.toast("Slow down!", icon=":material/bolt_boost:", duration=(datetime.now().timestamp() - st.session_state["LoginDebounce"]))
else:
    st.title("Overseer")
    # [ Section below quite literally serves 0 purpose apart from looking financially scary like a gamblers nightmare and dream combined. ]
    shares = 0
    dataList = [shares]

    @st.fragment(run_every=2)
    def showShares():
        global shares

        st.metric(label="Shares", value=shares, delta=shares - dataList[0])

        st.line_chart(data=dataList, x_label="Time", y_label="Shares")

        shares += randint(-50, 50)
        dataList.append(shares)
        if len(dataList) > 20:
            dataList.pop(0)

    showShares()

    st.header("Important manager stuff", divider=True)