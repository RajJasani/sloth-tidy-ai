import json
import sqlite3

def init_db():
    conn = sqlite3.connect("cache.db")
    conn.execute("CREATE TABLE IF NOT EXISTS tokens (id TEXT PRIMARY KEY, value TEXT)")
    conn.commit()
    return conn
