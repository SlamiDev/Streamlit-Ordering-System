# < Modules >
import streamlit as st
import yaml
import zmq
from datetime import datetime

st.cache_resource.clear()

# < Configs >
serverConfigPath = "C:/Users/Samuel Russo/Downloads/Python/OrderingSystem/BackEnd/ServerConfig.yaml"
serverConfig = yaml.load(open(serverConfigPath, "r", encoding="utf-8"), Loader=yaml.FullLoader)
settings = serverConfig["User Settings"]
Login_Directory = serverConfig["LoginDirectory"]
Login_Debounce = serverConfig["LoginDebounce"]
Create_Login_Protocol = serverConfig["CreateLoginProtocol"]
Create_Login_Port = str(serverConfig["CreateLoginPort"])

# < ZMQ Sockets >
@st.cache_resource(scope="session")
def createCreateLoginSocket():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"{Create_Login_Protocol}://127.0.0.1:{Create_Login_Port}")
    return socket

# < Session States >
if not "LoginDebounce" in st.session_state:
    st.session_state["LoginDebounce"] = round(datetime.now().timestamp())

socket = createCreateLoginSocket()

if "Done" in st.session_state: # [If a login has been made (page is reloaded due to streamlits functionality)]
    st.header(f"You have :green[successfully] made an account under the username of :violet[{st.session_state["Done"]}]")
else:
    st.title("Create Login") # [Format Page]
    with st.form("Create Login"):
        username = st.text_input("**Username:**", max_chars=settings["UsernameChars"], help="Cannot contain the symbol '/' or '%'!", key="Username", type="default", placeholder="Student123", icon=":material/badge:")
        password = st.text_input("**Password:**", max_chars=settings["PasswordChars"], help="Cannot contain the symbol '/'!", key="Password", type="password", placeholder="Password123", icon=":material/passkey:")

        if st.form_submit_button("Create", type="primary", icon=":material/check:", icon_position="left"):
            if (round(datetime.now().timestamp()) - st.session_state["LoginDebounce"]) >= Login_Debounce: # [Make sure no overloading]
                socket.send(f"{username}/{password}".encode("utf-8"))
                response = socket.recv().decode("utf-8")

                if response == "True":
                    st.session_state["Done"] = username
                    st.rerun()
                elif response == "Same":
                    st.toast(f"Username already in use!", icon=":material/error:", duration=5)
                else:
                    st.toast(f"Unable to create login, please try again later and not use the symbols '/' or '%'!", icon=":material/error:", duration=5)
                
                st.session_state["LoginDebounce"] = round(datetime.now().timestamp())
            else:
                st.toast("Slow down!", icon=":material/bolt_boost:", duration=(datetime.now().timestamp() - st.session_state["LoginDebounce"]))