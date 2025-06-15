# Vehicle Positions API Project
By Nils Wüstefeld and Adam Pasalek


## Summary
This Streamlit application visualizes delays from the Prague Public Transit Company and provides interactive visualizations and analytics. It features two dashboards: one focused on trip-level delays and another centered on delays at specific stops.
This allows users to gain insights into the performance of individual lines, identify bottlenecks in the network, and explore patterns in transit reliability over time and location.

To fetch historic the historic delays a proxy fetching server is obtaining the current delays for every minute and updates its database accordingly.

![Dataflow](images/dfp.drawio.png)






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
   This page serves as the home page for the application and gives a broad overview of all functions.


   From there navigate to the **connection** page and upload the environment file and the private key for the proxy server and API endpoint.

## Connection
   First upload the environment .env and press "Apply Enviroment" to update the settings with the data from the env.

   ![Set the Enviroment](images/environment1.png)







   In the second step you upload the .pem private key for the proxy server connection to enable realtime fetiching.
   After upload, press "Use Key" to update the Apps settings.
   Optionally you can check the keys validity with a key check.

   ![Enter your private Key](images/pem.png)



   If you're currently developing the app and have the .env and right private key in your apps folder, you can switch to "developer mode" and skip the uploads.

   
   After uploading you credentials, you can either go back to the landing page to update the internal database of the App or view the Dashboard and the Stops

## Sample Usage

   Go to the **Dashboard** or **Stops** page and pick a timeframe and minimum delay you want to examine. When you are ready, press **Apply**

   ![Enter the data in the form](images/form.png)

   After pressing apply, the Client will send a request to the proxy server and will visualize you data

   For example:

   ![Enter the data in the form](images/delay_mean_5min.png)











   
