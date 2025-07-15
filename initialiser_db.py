import sqlite3

conn = sqlite3.connect("stats.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS stats (
    user_id TEXT PRIMARY KEY,
    wins INTEGER DEFAULT 0,
    loses INTEGER DEFAULT 0,
    mvp_count INTEGER DEFAULT 0
)
""")

conn.commit()
conn.close()
print("✅ Base de données 'stats.db' créée avec succès")
