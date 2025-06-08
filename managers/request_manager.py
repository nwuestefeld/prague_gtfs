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
        """Establish an SSH connection to the remote database.

        Reads SSH_USER, SERVER_ADRESS, and PEM key path from environment/session state,
        then connects using Paramiko SSHClient.

        Raises:
            paramiko.SSHException: If SSH authentication or connection fails.
        """
        self.hostname = os.getenv("SERVER_ADRESS")
        self.username = os.getenv("SSH_USER")
        #self.key_path = "C:\\Users\\nilsw\\Documents\\prague_gtfs\\private_key_server.pem"
        #self.key = paramiko.RSAKey.from_private_key_file(self.key_path)
        self.key_path = st.session_state["pem_key_path"]
        self.remote_db_path ="vehicle_positions.db"
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(hostname=self.hostname, username=self.username, key_filename=self.key_path)


        
    def server_request(self, sql_query, columns=None):
        """Execute a SQL query on the remote SQLite database via SSH.

        Args:
            sql_query (str): The SQL query to run on the remote database.
            columns (list[str], optional): Column names for the returned DataFrame.

        Returns:
            pandas.DataFrame or None: A DataFrame with query results (empty if no data),
            or None if an error occurred.

        """
        print(sql_query)
        command = f"sqlite3 {self.remote_db_path} '{sql_query}'"
        stdin, stdout, stderr = self.ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()

        print("🧪 Raw output:")
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
                    "bearing",
                    "delay",
                    "latitude",
                    "longitude",
                    "state_position",
                    "timestamp"
                ]
            return df