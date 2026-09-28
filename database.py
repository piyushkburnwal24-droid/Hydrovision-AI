import sqlite3

def init_database():
    # Connect and create the local SQLite database table
    conn = sqlite3.connect("hydrovision_core.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            fixture TEXT,
            flow_lpm REAL,
            pressure_bar REAL,
            reynolds REAL,
            clog_pct REAL,
            status TEXT,
            monthly_waste_l REAL,
            cost_inr REAL
        )
    """)
    conn.commit()
    conn.close()

def save_audit(fixture, flow, pressure, reynolds, clog, status, waste, cost):
    # Save a new analysis run into the database
    conn = sqlite3.connect("hydrovision_core.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_records (fixture, flow_lpm, pressure_bar, reynolds, clog_pct, status, monthly_waste_l, cost_inr)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (fixture, flow, pressure, reynolds, clog, status, waste, cost))
    conn.commit()
    conn.close()

def load_audit_history():
    # Load all past records to display in the history tab
    conn = sqlite3.connect("hydrovision_core.db")
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, fixture, flow_lpm, pressure_bar, reynolds, clog_pct, status, cost_inr FROM audit_records ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows