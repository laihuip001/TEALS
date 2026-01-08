import sqlite3
import os
import sys

# プロジェクトルート検索
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
db_path = os.path.join(project_root, "data", "flow_audit.db")

print(f"Target DB: {db_path}")

if not os.path.exists(db_path):
    print("Database not found. Skipping migration (will be created fresh).")
    sys.exit(0)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # カラム存在チェック
    cursor.execute("PRAGMA table_info(audit_logs)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if "ai_model" in columns:
        print("Column 'ai_model' already exists.")
    else:
        print("Adding column 'ai_model'...")
        cursor.execute("ALTER TABLE audit_logs ADD COLUMN ai_model VARCHAR(50)")
        conn.commit()
        print("Migration successful.")
        
    conn.close()
except Exception as e:
    print(f"Migration failed: {e}")
    sys.exit(1)
