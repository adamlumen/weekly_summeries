#%%
import os
from dotenv import load_dotenv
import snowflake.connector as sf
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd
import yaml
import warnings
import time
from typing import Optional, Dict
import re

# Load environment variables
load_dotenv()

# --- Snowflake connection parameters from environment variables ---
def get_snowflake_settings():
    """Get Snowflake connection settings from environment variables."""
    return {
        "account": os.getenv("SNOWFLAKE_ACCOUNT", "skb61855.us-east-1"),
        "user": os.getenv("SNOWFLAKE_USER", "adam@lumen.me"),
        "role": os.getenv("SNOWFLAKE_ROLE", "ANALYSTS_TEAM_ROLE"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "ANALYST_WH"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "LUMEN_PROD"),
        "authenticator": os.getenv("SNOWFLAKE_AUTHENTICATOR", "externalbrowser")
    }
# --------------------------------------------------------------------

#%% snowflake stuff
def test_snowflake_connection(sf_settings=None):
    """Test connection to Snowflake database."""
    if sf_settings is None:
        sf_settings = get_snowflake_settings()
        
    try:
        # Establish connection to Snowflake
        ctx = sf.connect(**sf_settings)
        
        # Create cursor
        cs = ctx.cursor()
        
        # Execute a simple query to verify connection
        cs.execute("SELECT CURRENT_DATE()")
        result = cs.fetchone()
        
        print("Connection to Snowflake successful.")
        print("Current date in Snowflake:", result[0])

        # Close cursor and connection
        cs.close()
        ctx.close()
        return True
    except sf.Error as e:
        print("Error connecting to Snowflake:", e)
        return False

def extract_parameters_from_sql(query_path: str) -> list:
    """
    Extracts parameters enclosed in curly braces from a SQL script.

    Parameters:
    query_path (str): Path to the SQL script file.

    Returns:
    list: List of parameter names found in the SQL script.
    """
    with open(query_path, 'r') as f:
        sql_script = f.read()
    
    # Use regex to find all placeholders in the format {parameter_name}
    parameters = re.findall(r"\{(\w+)\}", sql_script)
    return parameters

def read_from_snowflake(query_path: str = "", parameters: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """
    Reads data from Snowflake based on a SQL query with dynamic placeholders.

    Parameters:
    query_path (str): Path to the SQL query file.
    parameters (Optional[Dict[str, str]]): Dictionary of parameters to replace placeholders in the query.

    Returns:
    pd.DataFrame: DataFrame containing the query results.
    """
    
    # Load the query from the file
    with open(query_path, 'r') as f:
        query = f.read()
    
    # Replace placeholders with parameters
    if parameters:
        query = query.format(**parameters)
    
    # Get Snowflake settings from environment
    sf_settings = get_snowflake_settings()
    
    # Establish connection to Snowflake
    with sf.connect(**sf_settings) as ctx:
        df_raw = pd.read_sql(query, ctx)
    
    return df_raw

def write_to_snowflake(df: pd.DataFrame, params: dict, overwrite: bool = False) -> bool:
    """
    Write DataFrame to Snowflake table.
    
    Parameters:
    df (pd.DataFrame): DataFrame to write
    params (dict): Dictionary with table, database, schema keys
    overwrite (bool): Whether to overwrite existing table
    
    Returns:
    bool: True if successful, False otherwise
    """
    # Get Snowflake settings from environment
    sf_settings = get_snowflake_settings()
    
    if not test_snowflake_connection(sf_settings):
        return False
    
    try:
        ctx = sf.connect(**sf_settings)
        
        write_pandas( 
            conn=ctx,
            df=df,
            table_name=params['table'],
            database=params['database'],
            schema=params['schema'],
            chunk_size=16000,
            auto_create_table=True,
            overwrite=overwrite
        )
        
        ctx.close()
        return True
    except Exception as e:
        print(f"Error writing to Snowflake: {e}")
        return False

#%% parameters handler
def get_params(param_file: str):

    with open(param_file) as f:
        params = yaml.full_load(f)
    return params
