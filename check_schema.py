import sqlite3

# Connect to the SQLite database
db_path = 'db.sqlite3'
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

# Check the schema of the zetaapp_kategori table
cursor.execute("PRAGMA table_info(zetaapp_kategori);")
columns = cursor.fetchall()

# Print the columns
for column in columns:
    print(column)

connection.close()