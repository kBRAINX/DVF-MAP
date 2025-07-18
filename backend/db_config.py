import psycopg2
import os

def get_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'management'),
        user=os.getenv('DB_USER', 'brayanne'),
        password=os.getenv('DB_PASSWORD', 'brayanne')
    )
