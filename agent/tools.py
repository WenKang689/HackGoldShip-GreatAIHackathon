from strands import Agent, tool
from strands.models import BedrockModel as StrandsBedrockModel
from strands.tools.mcp import MCPClient
from strands.types.tools import ToolResult, ToolUse
from mcp.client.streamable_http import streamablehttp_client
from config import SALESFORCE_ZAPIER_MCP_URL, STRIPE_MCP_URL, XERO_MCP_URL, MODEL_ID, WKHTMLTOPDF_PATH
from prompts import SALESFORCE_AGENT_PROMPT, REMINDER_AGENT_PROMPT
from typing import Any
import re
import copy
import json
import boto3
from datetime import datetime, timedelta
import pdfkit
import uuid
from jinja2 import Template
import requests
import base64

model = StrandsBedrockModel(model_id=MODEL_ID, region="us-east-1")

VALID_KEYS = {
    "account", "contact", "opportunity", "product", "products",
    "pricebook", "user", "missing_fields", "error"
}

def sanitize_salesforce_response(raw: str) -> dict:
    """
    Sanitize LLM response from Salesforce Agent.
    - Ensure valid JSON
    - Remove markdown, tables, or stray text
    - Enforce schema with only valid keys
    """
    try:
        # Strip markdown fences if present
        raw = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE)

        data = json.loads(raw)
    except Exception:
        return {"error": "Invalid JSON returned from Salesforce Agent."}

    if not isinstance(data, dict):
        return {"error": "Salesforce Agent did not return a JSON object."}

    # Filter keys to only valid schema
    sanitized = {k: v for k, v in data.items() if k in VALID_KEYS}

    # If everything got stripped, fallback
    if not sanitized:
        return {"error": "No valid Salesforce data fields returned."}

    return sanitized

def sanitize_property_name(prop_name):
    """Convert invalid property names to valid ones"""
    # Replace __COLON__ with underscore
    sanitized = prop_name.replace('__COLON__', '_')
    # Replace any other invalid patterns
    sanitized = re.sub(r'[^a-zA-Z0-9_.-]', '_', sanitized)
    # Limit to 64 characters
    return sanitized[:64]

def fix_tool_schema(tool):
    """Fix tool input schema to be Bedrock compatible"""
    try:
        if hasattr(tool, 'mcp_tool') and tool.mcp_tool.inputSchema:
            schema = tool.mcp_tool.inputSchema
            if isinstance(schema, dict) and 'properties' in schema:
                original_props = schema['properties']
                fixed_props = {}
                
                for prop_name, prop_value in original_props.items():
                    fixed_name = sanitize_property_name(prop_name)
                    fixed_props[fixed_name] = prop_value
                
                # Create new schema with fixed properties
                new_schema = copy.deepcopy(schema)
                new_schema['properties'] = fixed_props
                tool.mcp_tool.inputSchema = new_schema
                
        return tool
    except Exception as e:
        print(f"Error fixing tool schema: {e}")
        return tool

salesforce_mcp_client = MCPClient(lambda: streamablehttp_client(SALESFORCE_ZAPIER_MCP_URL))
xero_mcp_client = MCPClient(lambda: streamablehttp_client(XERO_MCP_URL))

@tool
def orchestratedInvoice(query: str) -> str:
    """
    Orchestration wrapper for invoice generation:
    1) Calls salesforceAgent(query) to fetch SF data (returns JSON string).
    2) Normalizes the products key so the preview always finds products.
    3) Passes sf_data (parsed dict) to generateInvoicePreview and returns that JSON.
    """
    sf_json = salesforceAgent(query)

    try:
        sf_data = json.loads(sf_json)
    except Exception:
        return json.dumps({
            "type": "error",
            "message": "Failed to parse Salesforce data from salesforceAgent."
        })

    if isinstance(sf_data, dict) and sf_data.get("error"):
        return json.dumps({"type": "error", "message": sf_data.get("error")})

    # Normalize products: ensure all line items are under "products" key
    if "opportunity" in sf_data and "line_items" in sf_data["opportunity"]:
        if "products" not in sf_data:
            sf_data["products"] = sf_data["opportunity"]["line_items"]

    # Now generate invoice preview
    return generateInvoicePreview(query, sf_data=sf_data)

@tool
def getSalesforceDetails(query: str) -> str:
    """
    Wrapper tool to fetch Salesforce account, contact, and opportunity details.
    Use this when the user only needs Salesforce info (not invoice).
    """
    sf_data = salesforceAgent(query)
    return json.dumps(sf_data, indent=2)

@tool
def salesforceAgent(query: str) -> str:
    """
    Query Salesforce safely via LLM + MCP.
    Returns validated JSON only.
    """
    try:
        with salesforce_mcp_client:
            tools = salesforce_mcp_client.list_tools_sync()
            fixed_tools = [fix_tool_schema(tool) for tool in tools]

            agent = Agent(
                system_prompt=SALESFORCE_AGENT_PROMPT,
                model=model,
                tools=fixed_tools
            )

            raw = str(agent(query))  # LLM actually queries Salesforce here
            sf_data = sanitize_salesforce_response(raw)
            return json.dumps(sf_data, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "error": f"Salesforce Agent failed: {str(e)}"
        }, indent=2)

@tool
def sendSNSEmail(query: str) -> str:
    
    try:
        # Initialize SNS client for ap-southeast-5 region
        sns_client = boto3.client('sns', region_name='ap-southeast-5')
        
        # Static topic ARN
        topic_arn = 'arn:aws:sns:ap-southeast-5:757834573545:HackathonTopic'
        
        # Parse the query to extract message details
        message_data = parse_message_query(query)
        
        # Send SNS message
        response = sns_client.publish(
            TopicArn=topic_arn,
            Message=message_data['message'],
            Subject=message_data.get('subject', 'Customer Notification')
        )
        
        return json.dumps({
            "status": "success",
            "message_id": response['MessageId'],
            "topic_arn": topic_arn,
            "message": message_data['message'],
            "subject": message_data.get('subject', 'Customer Notification'),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        error_msg = f"SNS messaging error: {str(e)}"
        print(f"ERROR: {error_msg}")
        return json.dumps({
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        })

def parse_message_query(query):
    """Parse message query to extract message and subject"""
    message_data = {
        'message': query,
        'subject': 'Customer Notification'
    }
    
    # Extract subject pattern
    subject_match = re.search(r'subject[:\s]+"([^"]+)"', query, re.IGNORECASE)
    if subject_match:
        message_data['subject'] = subject_match.group(1)
    
    # Extract message pattern
    message_match = re.search(r'message[:\s]+"([^"]+)"', query, re.IGNORECASE)
    if message_match:
        message_data['message'] = message_match.group(1)
    elif 'send' in query.lower():
        # Extract message after "send" keyword
        send_match = re.search(r'send\s+(.+)', query, re.IGNORECASE)
        if send_match:
            message_data['message'] = send_match.group(1)
    
    return message_data

@tool
def reminderAgent(query: str) -> str:
    agent = Agent(
        system_prompt=REMINDER_AGENT_PROMPT,
        model=model,
    )
   
    return str(agent(query))

@tool(name="generate_invoice_preview")
def generateInvoicePreview(query: str, sf_data: dict = None) -> str:
    if sf_data is None:
        return json.dumps({
            "type": "error",
            "message": "Missing Salesforce data. Please let the Orchestrator fetch Salesforce info first."
        }, indent=2)

    account = sf_data.get("account", {})
    contact = sf_data.get("contact", {})
    opportunity = sf_data.get("opportunity", {})

    # Build line items from products (priority: top-level products → product → opportunity.line_items)
    line_items = []
    total_amount = 0

    if sf_data.get("products"):
        line_items = [
            {
                "product": item.get("name", "Product"),
                "code": item.get("code", "N/A"),
                "qty": item.get("quantity", 1),
                "unit_price": item.get("unit_price", 0),
                "total": item.get("total_price", 0)
            }
            for item in sf_data["products"]
        ]
        total_amount = sum(item["total"] for item in line_items)

    elif sf_data.get("product"):
        product = sf_data["product"]
        line_items = [{
            "product": product.get("name", "Product"),
            "code": product.get("code", "N/A"),
            "qty": product.get("quantity", 1),
            "unit_price": product.get("unit_price", 0),
            "total": product.get("total_price", 0)
        }]
        total_amount = line_items[0]["total"]

    elif opportunity.get("line_items"):
        line_items = [
            {
                "product": item.get("product_name", "Product"),
                "code": item.get("product_code", "N/A"),
                "qty": item.get("quantity", 1),
                "unit_price": item.get("unit_price", 0),
                "total": item.get("total_price", 0)
            }
            for item in opportunity["line_items"]
        ]
        total_amount = sum(item["total"] for item in line_items)

    else:
        return json.dumps({
            "type": "error",
            "message": "No product data was found in Salesforce response."
        }, indent=2)

    # Dates & metadata
    invoice_id = f"DRAFT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
    issue_date = datetime.now().strftime("%Y-%m-%d")
    due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

    invoice_preview = {
        "type": "invoice_preview",
        "invoice_id": invoice_id,
        "status": "Draft",
        "issue_date": issue_date,
        "due_date": due_date,
        "account": account,
        "contact": contact,
        "line_items": line_items,
        "total_amount": total_amount,
        "currency": "USD",
        "actions": ["✓ Approve & Send Invoice PDF to Email"]
    }
    return json.dumps(invoice_preview, indent=2)

@tool
def updateInvoiceDatabase(tool: ToolUse, **kwargs: Any) -> ToolResult:
    import json
    from datetime import datetime
    
    tool_use_id = tool["toolUseId"]
    action = tool["input"]["action"]
    invoice_id = tool["input"]["invoice_id"]
    invoice_type = tool["input"]["invoice_type"]
    customer_name = tool["input"]["customer_name"]
    amount = tool["input"]["amount"]
    status = tool["input"]["status"]

    try:
        from model.accounting import InvoicePayment

        # Initialize payment model
        payment_model = InvoicePayment()
        
        if action == 'create':
            payment_id = payment_model.create_payment(
                invoice_id=invoice_id,
                customer_name=customer_name,
                amount=amount,
                invoice_type=invoice_type,
                status=status
            )

            return json.dumps({
                "status": "success",
                "action": "created",
                "invoice_id": invoice_id,
                "timestamp": datetime.now().isoformat()
            })
            
        elif action == 'update':
            payment_model.update_payment_status(
                invoice_id=invoice_id,
                status=status,
            )
            
            return json.dumps({
                "status": "success",
                "action": "updated",
                "payment_id": payment_id,
                "new_status": status,
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        error_msg = f"Payment update error: {str(e)}"
        print(f"ERROR: {error_msg}")
        return json.dumps({
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        })

@tool
def approveAndSendInvoice(query: str) -> str:
    """Generate PDF and send SNS email for approved invoice."""
    try:
        # Parse invoice JSON from query
        json_start = query.find('{')
        if json_start == -1:
            return json.dumps({"error": "No invoice data found"})

        invoice_json = query[json_start:]
        invoice_data = json.loads(invoice_json)

        # Step 1: Generate PDF
        pdf_result = sendInvoice(invoice_json)
        pdf_data = json.loads(pdf_result)

        # Step 2: Check PDF generation success
        if pdf_data.get("type") == "error":
            return pdf_result  # Stop here if PDF failed

        # Step 3: Prepare and send SNS email
        account_name = invoice_data.get("account", {}).get("name", "Customer")
        invoice_number = pdf_data.get("invoice_number", "Unknown")
        pdf_url = pdf_data.get("pdf_s3_url", "N/A")

        sns_message = (
            f"Invoice {invoice_number} has been generated for {account_name}. "
            f"PDF available at: {pdf_url}"
        )

        sns_result = sendSNSEmail(
            f'subject: "Invoice Generated" message: "{sns_message}"'
        )

        # Step 4: Return structured response
        return json.dumps({
            "type": "invoice_approved_sent",
            "invoice_number": invoice_number,
            "account": account_name,
            "pdf_url": pdf_url,
            "sns_status": json.loads(sns_result).get("status"),
            "message": f"Invoice {invoice_number} approved, PDF generated, and email notification sent"
        })

    except Exception as e:
        return json.dumps({
            "error": f"Failed to approve and send invoice: {str(e)}"
        })

@tool(name="send_invoice")
def sendInvoice(query: str) -> str:
    """
    Generate invoice PDF from HTML template stored in S3,
    assign final invoice number with UUID, upload PDF to S3,
    and return structured response including final HTML.
    """
    # 1. Parse invoice data JSON
    try:
        invoice_data = json.loads(query)
    except Exception as e:
        return json.dumps({
            "type": "error",
            "message": f"Invalid JSON input: {str(e)}"
        })

    # Get bucket region first
    s3_default = boto3.client("s3")
    try:
        response = s3_default.get_bucket_location(Bucket=S3_BUCKET_PDF)
        region = response.get('LocationConstraint') or 'us-east-1'
    except:
        region = 'us-east-1'
    
    s3 = boto3.client("s3", region_name=region, config=boto3.session.Config(signature_version='s3v4'))
    S3_BUCKET_PDF = "hackathon-generated-invoice-agent-pdf"
    S3_TEMPLATE_BUCKET = "hackathon-static-invoice-template"
    TEMPLATE_KEY = "invoice_template.html"

    # 2. Assign final invoice number
    today_str = datetime.now().strftime("%Y%m%d")
    unique_suffix = str(uuid.uuid4())[:8]
    invoice_number = f"INV-{today_str}-{unique_suffix}"
    invoice_data["invoice_number"] = invoice_number
    invoice_data["invoice_id"] = invoice_number

    # 3. Fetch HTML template from S3
    try:
        template_obj = s3.get_object(Bucket=S3_TEMPLATE_BUCKET, Key=TEMPLATE_KEY)
        template_content = template_obj['Body'].read().decode('utf-8')
        template = Template(template_content)

        # Render template with invoice data
        html_content = template.render(invoice=invoice_data)
    except Exception as e:
        return json.dumps({
            "type": "error",
            "message": f"Template fetching/rendering failed: {str(e)}"
        })

    # 4. Convert HTML to PDF
    try:
        config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
        options = {
            'enable-local-file-access': None,
            'load-error-handling': 'ignore',
            'load-media-error-handling': 'ignore',
            'no-stop-slow-scripts': None,
            'debug-javascript': None,
            'javascript-delay': 1000
        }
        pdf_bytes = pdfkit.from_string(html_content, False, configuration=config, options=options)
    except Exception as e:
        return json.dumps({
            "type": "error",
            "message": f"PDF generation failed: {str(e)}"
        })

    # 5. Upload PDF via API Gateway with fallback to direct S3
    file_key = f"invoices/{invoice_number}.pdf"
    presigned_url = None
    
    try:
        # Try API Gateway first
        api_endpoint = "https://14kxucu9dh.execute-api.ap-southeast-5.amazonaws.com/get-presigned-url"
        payload = {
            "fileName": f"{invoice_number}.pdf",
            "fileContent": base64.b64encode(pdf_bytes).decode('utf-8'),
            "contentType": "application/pdf"
        }
        
        response = requests.post(api_endpoint, json=payload, timeout=30)
        
        if response.status_code == 200:
            api_response = response.json()
            presigned_url = api_response.get('downloadUrl')
            
    except Exception as api_error:
        print(f"API Gateway failed: {api_error}")
        
    # Fallback to direct S3 upload if API Gateway failed
    if not presigned_url:
        try:
            s3.put_object(
                Bucket=S3_BUCKET_PDF,
                Key=file_key,
                Body=pdf_bytes,
                ContentType="application/pdf"
            )
            
            presigned_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": S3_BUCKET_PDF, "Key": file_key},
                ExpiresIn=86400
            )
            
        except Exception as s3_error:
            return json.dumps({
                "type": "error",
                "message": f"Both API Gateway and S3 upload failed: {str(s3_error)}"
            })

    # 7. Return structured response
    return json.dumps({
        "type": "invoice_sent",
        "invoice_number": invoice_number,
        "account": invoice_data.get("account", {}).get("name", "Unknown"),
        "contact": invoice_data.get("contact", {}).get("name", "Unknown"),
        "pdf_s3_url": presigned_url,
        "final_html": html_content,
        "status": "Invoice PDF uploaded to S3"
    }, indent=2)
