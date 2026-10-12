import sqlite3

def setup_database():
    # 1. Create and connect to the local SQLite database
    conn = sqlite3.connect('supplier_intelligence.db')
    cursor = conn.cursor()

    # 2. Create a table specifically tailored to Exiger's domain (Risk & Compliance)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        location TEXT,
        risk_score INTEGER, 
        compliance_status TEXT,
        last_audit_date TEXT
    )
    ''')

    # Clear existing data just in case you run this script twice
    cursor.execute('DELETE FROM suppliers')

    # 3. Insert mock supply chain data (notice the variety in risk statuses)
    suppliers = [
        ('TechParts Inc.', 'Shenzhen, China', 85, 'High Risk - Pending Audit', '2023-11-12'),
        ('Global Circuits Ltd.', 'Taiwan', 20, 'Compliant', '2024-02-15'),
        ('Acme Logistics', 'Chicago, USA', 45, 'Moderate - Watchlist', '2024-01-05'),
        ('Quantum Semiconductors', 'Berlin, Germany', 15, 'Compliant', '2024-03-20'),
        ('Nexus Metals', 'DRC', 92, 'Critical - ESG Violation', '2023-08-30')
    ]

    cursor.executemany('''
    INSERT INTO suppliers (company_name, location, risk_score, compliance_status, last_audit_date)
    VALUES (?, ?, ?, ?, ?)
    ''', suppliers)

    conn.commit()
    print("✅ Database 'supplier_intelligence.db' created successfully.")
    
    # 4. Print the data to verify it worked
    print("\n--- Current Supplier Database ---")
    cursor.execute("SELECT * FROM suppliers")
    for row in cursor.fetchall():
        print(f"Name: {row[1]} | Risk Score: {row[3]} | Status: {row[4]}")

    conn.close()

if __name__ == "__main__":
    setup_database()
