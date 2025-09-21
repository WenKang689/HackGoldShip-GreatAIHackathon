import os
import platform

SALESFORCE_ZAPIER_MCP_URL ="https://mcp.zapier.com/api/mcp/s/NDgzZmM0ODQtMmViOC00NzQ0LThjYzQtM2NmMmI4ZDNmZThhOjA5YjczM2UyLWMwMDgtNDBlYy1iNjQ2LTFjZTliZTg4Yzk3Mg==/mcp"
STRIPE_MCP_URL = ""
XERO_MCP_URL = "https://mcp.zapier.com/api/mcp/s/MWIzNDI3YTgtZmQzNi00YzBkLWEwNmMtY2JkMjVmMWZjMjViOjQ3NjRmZDU2LWY2NjQtNDVlOS1iZjE0LWE5ZDQ3YmQ2MDI2MQ==/mcp"
MODEL_ID = "us.anthropic.claude-opus-4-1-20250805-v1:0"

# Auto-detect wkhtmltopdf path based on OS
def get_wkhtmltopdf_path():
    if os.getenv("WKHTMLTOPDF_PATH"):
        return os.getenv("WKHTMLTOPDF_PATH")
    
    system = platform.system()
    if system == "Windows":
        return r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    elif system == "Darwin":  # macOS
        return "/usr/local/bin/wkhtmltopdf"
    else:  # Linux
        return "/usr/bin/wkhtmltopdf"

WKHTMLTOPDF_PATH = get_wkhtmltopdf_path()
