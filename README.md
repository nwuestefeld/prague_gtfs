# Vehicle Positions API Project

This project fetches realtime vehicle positions from the Prague Public Transit Company and provides visualisations and analytics of the trips and stops.
To fetch vehicle positions and sationary data, the project uses the following API:

- **API URL**: `https://api.golemio.cz/pid/docs/openapi/` 



By Nils Wüstefeld and Adam Pasalek


## Setup Instructions

### Requirements

To run this project, you need to install the required Python dependencies and obtain the `.env` file and `server key` from the admin.
These dependencies are listed in the `requirements.txt` file. You can install them using `pip`:

1. **Create a Virtual Environment** (if you don't have one already):

   ```bash
   python -m venv venv
    ```

2. **Active the Venv**
   ### Linux
    ```bash
    source meinenv/bin/activate
    ```
    
    ### Windows
    ```powershell
    venv\Scripts\Activate.ps1
    ```

3. **Install the requirements**
   ```bash
   pip install -r requirements.txt
    ```

4. **Get Enviroment file .env and .pem from the admin or optionally build your own**: the .env file should look like this:
    ```bash
    API_KEY=your_api_key_here
    API_URL=https://your-api-url.com/endpoint
    SERVER_ADRESS = "12345.123"
    USER = "your username"
    ```
5. **Run with Streamlit**:
   ```bash
   python -m streamlit run main.py

   ```
## Start the Application
   After running the application, you will land on the landing page.
   From there navigate to the Settings page and upload the environment file and the private key for the fetching proxy
   First upload the enivironment .env and press "apply" to update the apps settings with the data from the env.

   In the second step you upload the private key to the proxy server to enable realtime fetiching.
   After upload, press "Use Key" to update the Apps settings.
   Optionally you can check the keys validity with a key check.

   If you're currently developing the app and have the .env and right private key in your apps folder, you can switch to "developer mode" and skip the uploads.

## Dashboard

## Stops

## Map








   
