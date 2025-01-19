import sqlite3
import os

db_path = 'issues.db'

if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Deleted existing database file: {db_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute('''CREATE TABLE issues
             (uuid TEXT PRIMARY KEY, email TEXT, numphone TEXT, date TEXT, departement TEXT, salle TEXT, type TEXT, description TEXT, photo TEXT, sender TEXT, valid INT, technicien TEXT, dueto TEXT)''')

conn.commit()
conn.close()

print(f"Created new database file: {db_path}")