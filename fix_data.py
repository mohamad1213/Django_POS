import sqlite3

# Connect to the SQLite database
db_path = 'db.sqlite3'
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

# Fix invalid owner_id values
cursor.execute("""
UPDATE zetaapp_kategori
SET owner_id = NULL
WHERE owner_id NOT IN (SELECT id FROM auth_user);
""")

# Commit changes and close the connection
connection.commit()
connection.close()

print("Invalid owner_id values have been fixed.")