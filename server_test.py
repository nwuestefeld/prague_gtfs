### TESTSKRIPT for SHH DATABASE CONNECTION 
### DO NOT RUN THIS SCRIPT
### THIS SCRIPT IS FOR TESTING PURPOSES ONLY


import paramiko
import pandas as pd
from io import StringIO
import sqlite3
import os
from dotenv import load_dotenv

#Connection setup
load_dotenv()
hostname = os.getenv("SERVER_ADRESS")
username = os.getenv("USER")            
key_path = "C:\\Users\\nilsw\\Documents\\prague_gtfs\\private_key_server.pem"
key = paramiko.RSAKey.from_private_key_file(key_path)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=hostname, username=username, key_filename=key_path)
#Query: TODO: Adjust query for modular requests: fetch all vehicle positions from last 20 min, ...
#classification: TODO: Add classification for vehicle positions: center, outskirts, ...
#TODO: add gtfs_trip_id. über trip_id bekomm ich die richtung und  route_id, da bekomme ich die restlichen infos
sql_query = """
SELECT 
    vehicle_id, 
    gtfs_trip_id,
    gtfs_route_short_name, 
    AVG(delay) AS delay, 
    timestamp 
FROM vehicle_positions 
GROUP BY gtfs_trip_id
ORDER BY mean_delay DESC 
LIMIT 20;
"""


#db on server
remote_db_path = "vehicle_positions.db"

#command
command = f"sqlite3 {remote_db_path} '{sql_query}'"
stdin, stdout, stderr = ssh.exec_command(command)
output = stdout.read().decode()
error = stderr.read().decode()


if error:
    print("Error:", error)
else:
    # Test DB
    df = pd.read_csv(StringIO(output), sep="|")
    #print(df)
    print(df.info())
    print(df.head())

ssh.close()
