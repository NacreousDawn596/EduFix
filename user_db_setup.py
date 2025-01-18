import sqlite3
import os

db_path = 'users.db'

if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Deleted existing database file: {db_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute('''CREATE TABLE users
             (username TEXT PRIMARY KEY, password TEXT, email TEXT, phonenum TEXT, position INT, dep TEXT)''')

users = [
    ("nifnif", "1234", "nifnif@yahoo.yay", "+9699975", 0, ""),
    ("headadmin", "1234", "idk@ab", "+212344", 2, "Maths Info")
]

c.executemany('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)', users)

conn.commit()
conn.close()

print(f"Created new database file: {db_path}")