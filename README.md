# Vehicle Positions API Project

This project fetches vehicle positions from an API and stores them in a database for efficient querying and access. The data is periodically fetched every 30 seconds and stored in an SQLite database. You can interact with the database via a simple API endpoint.

## API Endpoint

To fetch vehicle positions, the project uses the following API:

- **API URL**: `Yhttps://api.golemio.cz/pid/docs/openapi/` 

## Setup Instructions

### Requirements

To run this project, you need to install the required Python dependencies. These dependencies are listed in the `requirements.txt` file. You can install them using `pip`:

1. **Create a Virtual Environment** (if you don't have one already):

   ```bash
   python -m venv venv
    ```

2. **Active the Venv**

3. **Install the requirements**
   ```bash
   pip install -r requirements.txt
    ```


4. **Setup Environment file .env** and include in .gitignore (!!!!!!!!!)
    ```bash
    API_KEY=your_api_key_here
    API_URL=https://your-api-url.com/endpoint
    ```
5. **Run with Streamlit**:
   ```bash
   python -m streamlit run main.py

   ```





   
