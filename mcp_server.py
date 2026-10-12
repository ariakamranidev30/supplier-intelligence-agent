import sqlite3
from mcp.server.fastmcp import FastMCP

# 1. Initialize the MCP Server
mcp = FastMCP("SupplierIntelligence")

# 2. The @mcp.tool() decorator automatically turns this function into an AI tool
@mcp.tool()
def get_supplier_risk(company_name: str) -> str:
    """Retrieve the risk score, compliance status, and audit date for a specific supplier."""
    try:
        conn = sqlite3.connect('supplier_intelligence.db')
        cursor = conn.cursor()
        
        # Use LIKE to make the search a bit more forgiving for the AI
        cursor.execute(
            "SELECT risk_score, compliance_status, last_audit_date, location FROM suppliers WHERE company_name LIKE ?", 
            (f"%{company_name}%",)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            risk_score, status, last_audit, location = result
            return f"Supplier: {company_name} ({location})\nRisk Score: {risk_score}/100\nStatus: {status}\nLast Audit: {last_audit}"
        else:
            return f"Error: Supplier '{company_name}' not found in the database."
    except Exception as e:
        return f"Database error: {str(e)}"

@mcp.tool()
def list_all_suppliers() -> str:
    """Get a list of all known suppliers in the system."""
    try:
        conn = sqlite3.connect('supplier_intelligence.db')
        cursor = conn.cursor()
        cursor.execute("SELECT company_name, compliance_status FROM suppliers")
        results = cursor.fetchall()
        conn.close()
        
        if results:
            return "\n".join([f"- {name} (Status: {status})" for name, status in results])
        return "No suppliers found."
    except Exception as e:
        return f"Database error: {str(e)}"

if __name__ == "__main__":
    # MCP servers communicate securely over standard input/output (stdio)
    mcp.run()
