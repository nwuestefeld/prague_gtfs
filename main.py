from client import Client
import streamlit as st


def main(): 
    #setup database 
    client = Client()
    #init steamlit
    #st.title("Prague GTFS Data")
    #st.sidebar.title("Navigation")
    st.title("Login Page")
   
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        # TODO authlogic
        if username == "admin" and password == "admin":
            st.success("Login successful!")
            st.session_state["logged_in"] = True
            #st.experimental_rerun()
        else:
            st.error("Invalid username or password")
    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        st.success("You are logged in!")
        st.sidebar.success("You are logged in!")
        st.sidebar.title("Navigation")
        st.sidebar.write("Welcome to the app!")
        st.sidebar.write("Please select a page from the sidebar.")


if __name__ == "__main__":
    main()