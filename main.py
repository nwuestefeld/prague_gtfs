from client import Client
import streamlit as st


import streamlit as st

def show_login():
    st.title("Login Page")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "admin":
            st.session_state["logged_in"] = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password")

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        show_login()
    else:
        st.title("Welcome to the GTFS App!")
        st.sidebar.success("You are logged in!")
        st.sidebar.info("Navigate using the sidebar.")
        st.write("This is the home page after login.")

        if st.button("Refresh Data"):
            client = Client()
            with st.spinner("loading data..."):
                client.run()
            st.success("Your database is up to date!")
if __name__ == "__main__":
    main()