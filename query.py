# pip install streamlit
# pip install mysql-connector-python

import mysql.connector
import pandas as pd

def connection(query):
    conn = mysql.connector.connect(
        host="projeto-integrador-grupo8.mysql.database.azure.com",
        port="3306",
        user="grupo8",
        password="Senai@134",
        db="db_aqi"
    )
    
    dataframe = pd.read_sql(query, conn)
    # Executar o SQL e armazenar o resultado no dataframe
    
    conn.close()
    
    return dataframe

