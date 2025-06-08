import os
from dotenv import load_dotenv

load_dotenv()

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

    if dev_mode := st.checkbox("Developer Mode", value=False):
        st.info("Developer mode is enabled.")
        api_key = os.getenv("API_KEY")
        st.session_state["api_key"] = api_key
    else:
        st.info("Developer mode is disabled.")
        api_key = st.text_input("Enter your API key", type="password")
        if st.button("Save API Key"):
            if api_key:
                st.session_state["api_key"] = api_key
                st.success("API key saved successfully.")
            else:
                st.error("Please enter a valid API key.")

        if not api_key:
            st.warning("Please enter your API key to proceed.")
            return

    st.write("### PEM Key Upload")
    hostname = os.getenv("SERVER_ADRESS")
    username = os.getenv("SSH_USER")

    st.write(f"🌐 **Host:** `Python Server Nils`")
    st.write(f"👤 **User:** `{username}`")
    st.markdown("Upload your PEM key below:")

    uploaded_file = st.file_uploader("Upload `.pem` file", type=["pem"])

    if uploaded_file is not None:
        key_data = uploaded_file.read()
        try:
            pem_content = key_data.decode("utf-8")
        except UnicodeDecodeError:
            st.error("Failed to decode PEM file. Please upload a valid PEM file.")
            return

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
                ssh.connect(hostname=hostname, username=username, key_filename=key_path)
                st.success("Connection successful!")
                ssh.close()
            except Exception as e:
                st.error(f"Connection failed: {e}")


if __name__ == "__main__":
    settings_page()
