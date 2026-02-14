import mysql.connector
import psycopg2
from psycopg2.extras import execute_values
import os

# Legacy MySQL
MYSQL_CONFIG = {
    'host': 'mysql-scheduler.jupyter.dev.local',
    'user': 'root',
    'password': 'secret',
    'database': 'crawler_control'
}

# New Postgres
PG_CONFIG = {
    'host': 'archive_postgres',
    'user': 'postgres',
    'password': 'secret',
    'dbname': 'archive_system'
}

def migrate():
    mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
    pg_conn = psycopg2.connect(**PG_CONFIG)
    
    # Tables to migrate
    # Format: (source_db, source_table, target_schema, target_table)
    migrations = [
        ('crawler_control', 'users', 'control', 'users'),
        ('crawler_control', 'targets', 'control', 'targets'),
        ('crawler_control', 'user_subscriptions', 'control', 'user_subscriptions'),
        ('crawler_control', 'crawl_jobs', 'control', 'crawl_jobs'),
        ('archive_system', 'imageboard_curation', 'control', 'curation'),
    ]
    
    try:
        pg_cur = pg_conn.cursor()
        
        for src_db, src_table, tgt_schema, tgt_table in migrations:
            print(f"Migrating {src_db}.{src_table} to {tgt_schema}.{tgt_table}...")
            
            try:
                mysql_conn.database = src_db
                mysql_cur = mysql_conn.cursor(dictionary=True)
                mysql_cur.execute(f"SELECT * FROM {src_table}")
                rows = mysql_cur.fetchall()
                mysql_cur.close()
            except Exception as e:
                print(f"Skipping {src_db}.{src_table}: {e}")
                continue
            
            if not rows:
                print(f"Table {src_table} is empty.")
                continue
                
            columns = rows[0].keys()
            # Special handling for column renames if any
            if tgt_table == 'curation' and 'id' in columns:
                # keep id or let postgres generate? usually better to keep for referential integrity if any
                pass
                
            cols_str = ", ".join(columns)
            
            # Convert types for Postgres
            data = []
            for row in rows:
                processed_row = []
                for k, v in row.items():
                    if k in ['is_active', 'moderated', 'enabled', 'break_into_steps']:
                        processed_row.append(bool(v))
                    else:
                        processed_row.append(v)
                data.append(tuple(processed_row))
                
            execute_values(pg_cur, f"INSERT INTO {tgt_schema}.{tgt_table} ({cols_str}) VALUES %s ON CONFLICT DO NOTHING", data)
            print(f"Migrated {len(rows)} rows.")
            
        pg_conn.commit()
    finally:
        mysql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
