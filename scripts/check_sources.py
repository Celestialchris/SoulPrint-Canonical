import sqlite3
conn = sqlite3.connect('instance/soulprint.db')
cur = conn.cursor()
cur.execute("SELECT source, COUNT(*) FROM imported_conversation GROUP BY source")
for row in cur.fetchall():
    print(f"{row[0]}: {row[1]}")
