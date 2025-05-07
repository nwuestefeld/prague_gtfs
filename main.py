from client import Client
import streamlit as st


def main(): 
   

    #setup database 
    client = Client()
    #init steamlit
    st.title("Prague GTFS Data")


if __name__ == "__main__":
    main()