import psycopg
import os
from dotenv import load_dotenv
load_dotenv()

conn = psycopg.connect(os.environ[f"{os.getenv('SUPABASE_DB_URL')}"])  # paste your connection string

with conn.cursor() as cur:
    cur.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name;
    """)
    for row in cur.fetchall():
        print(row)
