import paramiko
import pandas as pd
from io import StringIO
import sqlite3
import os
from dotenv import load_dotenv

class RequestManager:
    def __init__(self):
        self.load_env()
        self.hostname = os.getenv("SERVER_ADRESS")
        self.username = os.getenv("USER")
        self.key_path = os.getenv("KEY_PATH")
        self.remote_db_path ="vehicle_positions.db"
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(hostname=self.hostname, username=self.username, key_filename=self.key_path)

    
    def load_env(self):
        load_dotenv()
        
    def server_request(self, sql_query):
        """
        Executes a SQL query on the remote SQLite database and returns the result as a pandas DataFrame.
        """
        command = f"sqlite3 {self.remote_db_path} '{sql_query}'"
        stdin, stdout, stderr = self.ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()

        if error:
            print("Error:", error)
            return None
        else:
            df = pd.read_csv(StringIO(output))
            return df