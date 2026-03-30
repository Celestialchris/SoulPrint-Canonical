import sqlite3
conn = sqlite3.connect('instance/soulprint.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
for row in cur.fetchall():
    print(row[0])
print('---')
for table in ['imported_conversation', 'imported_message', 'ImportedConversation', 'ImportedMessage']:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"{table}: {cur.fetchone()[0]} rows")
    except:
        pass
conn.close()
