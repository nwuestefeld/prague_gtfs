import os
from dotenv import load_dotenv


"""Connections page for configuring API and SSH settings to access GTFS data.

This module provides a Streamlit page where users can enter their API key for static GTFS endpoints,
upload a PEM file for SSH access to real-time vehicle position data, and test the connection.
"""

import streamlit as st
import tempfile
import paramiko


def settings_page():
    """Render the Connections page for GTFS data configuration.

    Displays controls for:
    1. Entering or loading the API key (static GTFS).
    2. Uploading a PEM key for SSH access (real-time data).
    3. Testing the SSH connection.
    """
    st.title("Connections Page")
    st.markdown("""
    **Connection Setup**  
    Before you can fetch static or real-time GTFS data, you need:

    1. **API Key** – provides access to the static GTFS endpoint.  
    2. **PEM Key** – establishes SSH connection to the realtime vehicle-positions server.

    - Toggle **Developer Mode** to load your API key from `.env`.  
    - Upload your `.pem` file, then click **Connection Test** to verify connectivity.

    > **Security Notice**  
    > Keep your PEM key **confidential**. Do not share it with unauthorized users.

    For questions or assistance, contact your **system administrator**.
    """, unsafe_allow_html=True)

    st.write("### Connection Settings")
    st.markdown("Please enter your API key to access the static GTFS data.")

    dev_mode = st.checkbox("Developer Mode", value=False)

    if dev_mode:
        load_dotenv()
        st.info("Developer mode is enabled. Using API key and PEM key from environment variables. " \
        "(Please know what you are doing!)")
        st.session_state["api_key"] = os.getenv("API_KEY")
        st.session_state["pem_key_path"] = "private_key_server.pem"
        st.session_state["SSH_USER"] = os.getenv("SSH_USER")
        st.session_state["SERVER_ADDRESS"] = os.getenv("SERVER_ADDRESS")
        st.session_state["API_URL"] = os.getenv("API_URL")
    else:
        st.info("Developer mode is disabled. Please upload your .env file and upload PEM key.")
    
        #TODO: Add .env file upload option
        st.write("### Environment Variables Upload")

        st.markdown("""
        You can upload a `.env` file to set your environment variables.
        This file should contain your API key and other necessary configurations.
        """)
        env_file = st.file_uploader("Upload `.env` file", type=["env"])
        if env_file is not None:
            try:
                env_content = env_file.read().decode("utf-8")
                with open(".env", "w") as f:
                    f.write(env_content)
                st.success("Environment variables loaded successfully.")
            except Exception as e:
                st.error(f"Failed to load environment variables: {e}")
            if st.button("Apply Environment"):
                st.info("Applying environment variables from `.env` file...")
                load_dotenv()
                st.write("API_KEY from os.getenv:", os.getenv("API_KEY"))
                st.write("SSH_USER from os.getenv:", os.getenv("USER"))
                st.write("SERVER_ADDRESS from os.getenv:", os.getenv("SERVER_ADDRESS"))
                st.session_state["api_key"] = os.getenv("API_KEY")
                #st.session_state["pem_key_path"] = "private_key_server.pem"
                st.session_state["SSH_USER"] = os.getenv("USER")
                st.session_state["SERVER_ADDRESS"] = os.getenv("SERVER_ADDRESS")
                st.session_state["API_URL"] = os.getenv("API_URL")


        # PEM-Key
  
        st.write("### PEM Key Upload")
        st.write(f"🌐 **Host:** `Python Server Nils`")
        st.write(f"👤 **User:** `USER`")
        st.markdown("Upload your PEM key below:")

        uploaded_file = st.file_uploader("Upload `.pem` file", type=["pem"])

        if uploaded_file is not None:
            key_data = uploaded_file.read()
            try:
                pem_content = key_data.decode("utf-8")
            except UnicodeDecodeError:
                st.error("Failed to decode PEM file. Please upload a valid PEM file.")
                st.stop()

            st.text_area("PEM File Content:", pem_content, height=300)
            st.success("PEM file is ready to use.")

            if st.button("Use Key"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pem") as temp_key_file:
                    temp_key_file.write(key_data)
                    temp_key_file_path = temp_key_file.name
                os.chmod(temp_key_file_path, 0o400)

                st.session_state["pem_key_content"] = pem_content
                st.session_state["pem_key_path"] = temp_key_file_path
                st.success(f".pem file saved temporarily at:\n`{temp_key_file_path}`")

        if st.button("Connection Test"):
            if "pem_key_path" not in st.session_state:
                st.error("Please upload a PEM key first.")
            else:
                try:
                    key_path = st.session_state["pem_key_path"]
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    hostname = st.session_state.get("SERVER_ADDRESS")
                    username = st.session_state.get("SSH_USER")
                    if not hostname or not username:
                        st.error("Please set the server address and SSH user in the environment variables.")
                        return
                    ssh.connect(hostname=hostname, username=username, key_filename=key_path)
                    st.success("Connection successful!")
                    ssh.close()
                except Exception as e:
                    st.error(f"Connection failed: {e}")


if __name__ == "__main__":
    settings_page()
