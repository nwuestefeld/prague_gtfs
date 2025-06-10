import paramiko
import pandas as pd
from io import StringIO
import sqlite3
import os
from dotenv import load_dotenv
import streamlit as st

class RequestManager:
    """Manages SSH connection and SQL queries to the remote vehicle_positions database.

    This class loads environment variables, opens an SSH tunnel to the remote SQLite database,
    and provides methods to execute SQL queries and return results as pandas DataFrames.
    """
    def __init__(self):
        """Initialize the RequestManager.

        Loads environment variables and establishes an SSH connection to the remote database.
        """
        self.load_env()
        self.connect()



 
    
    def load_env(self):
        """Load environment variables from a .env file."""
        load_dotenv()


    def connect(self):

        #TODO: connect to settings

        """Establish an SSH connection to the remote database.

        Reads SSH_USER, SERVER_ADRESS, and PEM key path from environment/session state,
        then connects using Paramiko SSHClient.

        Raises:
            paramiko.SSHException: If SSH authentication or connection fails.
        """
        if "SERVER_ADDRESS" not in st.session_state or "SSH_USER" not in st.session_state or "pem_key_path" not in st.session_state:
            st.error("Please set the SERVER_ADDRESS, SSH_USER, and pem_key_path in the session state.")
            print("Missing session state variables: SERVER_ADDRESS, SSH_USER, or pem_key_path")
            return
        self.hostname = st.session_state["SERVER_ADDRESS"]
        self.username = st.session_state["SSH_USER"]
        print("Connecting to server:", self.hostname)
        print("Using username:", self.username)

        #self.key_path = "C:\\Users\\nilsw\\Documents\\prague_gtfs\\private_key_server.pem"
        #self.key = paramiko.RSAKey.from_private_key_file(self.key_path)
        self.key_path = st.session_state["pem_key_path"]
        #print("Using key path:", self.key_path)
        self.remote_db_path ="vehicle_positions.db"
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(hostname=self.hostname, username=self.username, key_filename=self.key_path)
        except paramiko.SSHException as e:
            st.error("SSH connection failed. Please check your credentials and server address.")
            print("SSH connection failed:", e)
            return

    def server_request(self, sql_query, columns=None):
        """Execute a SQL query on the remote SQLite database via SSH.

        Args:
            sql_query (str): The SQL query to run on the remote database.
            columns (list[str], optional): Column names for the returned DataFrame.

        Returns:
            pandas.DataFrame or None: A DataFrame with query results (empty if no data),
            or None if an error occurred.

        """

        safe_query = sql_query.replace("'", "'\"'\"'") #this line = 1 sleepless night
        #print("Executing SQL query on remote database:")
        #print(safe_query)
        if self.remote_db_path is None or not self.remote_db_path:
            st.error("Please input the setting files or check the connection.")
            return None
        command = f"sqlite3 {self.remote_db_path} '{safe_query}'"
        stdin, stdout, stderr = self.ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()

        print(repr(output))

        if error:
            print("Error:", error)
            return None
        else:
            if not output.strip():
                print("No data returned from the query.")
                df = pd.DataFrame()
            else:
                df = pd.read_csv(StringIO(output), sep="|", header=None)
                #print(df.head())

                if columns is not None:
                    if len(columns) == df.shape[1]:
                        df.columns = columns
                else:
                    df.columns = [
                    "vehicle_id",
                    "gtfs_trip_id",
                    "route_type",
                    "gtfs_route_short_name",
                    "delay",
                    "bearing",
                    "latitude",
                    "longitude",
                    "state_position",
                    "timestamp"
                ]
            return df