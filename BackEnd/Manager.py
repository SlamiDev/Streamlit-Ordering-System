# < Modules >
import streamlit as st
import yaml
from pathlib import Path

st.cache_resource.clear()

parentDirectory = current_dir = Path(__file__).resolve().parent
ancestorDirectory = parentDirectory.parent

# < Configs >
serverConfigPath = parentDirectory / "ServerConfig.yaml"
serverConfig = yaml.load(open(serverConfigPath, "r", encoding="utf-8"), Loader=yaml.FullLoader)

pages = []
# [ List all pages ]
for primLocation in serverConfig["Pages"]:
    for secoLocation in serverConfig["Pages"][primLocation]:
        pageLocation = ancestorDirectory / primLocation / secoLocation
        sections = str(pageLocation).split("\\")
        end = sections[len(sections) - 1]
        pageTitle = end[0:end.find(".")]

        selectedIcon = ":material/menu:"

        if pageTitle == "ManagerHome":
            pageTitle = "Home"
            selectedIcon = ":material/home:"
        elif pageTitle == "CreateManagerLogin":
            pageTitle = "Create Login"
            selectedIcon = ":material/login:"

        completedString = pageTitle[0]

        for pageTitleChar in pageTitle[1:]:
            if pageTitleChar.isupper():
                completedString += f" {pageTitleChar}"
            else:
                completedString += pageTitleChar

        pages.append(st.Page(pageLocation, title=completedString, icon=selectedIcon))

control = st.navigation(pages, position="sidebar", expanded=True)
control.run()