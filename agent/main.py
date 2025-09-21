from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from agents import create_orchestrator_agent
import uuid
import boto3
import json
import re
import requests
import os

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track processed messages to prevent duplicates
processed_messages = set()

# SNS client for payment notifications
sns_client = boto3.client('sns', region_name='ap-southeast-5')
TOPIC_ARN = 'arn:aws:sns:ap-southeast-5:757834573545:HackathonTopic'

@app.websocket("/ws/admin")
async def admin_websocket(websocket: WebSocket):
    await websocket.accept()
    
    # Generate unique session ID for this WebSocket connection
    session_id = f"admin-{uuid.uuid4()}"
    agent = create_orchestrator_agent(session_id)
    
    print(f"Admin session started: {session_id}")
    
    try:
        while True:
            message = await websocket.receive_text()
            try:
                response = str(agent(message))
                # Clean invoice preview responses - extract everything after </thinking>
                if '"type": "invoice_preview"' in response:
                    thinking_end = response.find('</thinking>')
                    if thinking_end != -1:
                        response = response[thinking_end + len('</thinking>'):].strip()
                    
                    # Remove markdown code blocks
                    response = re.sub(r'^```json\s*|\s*```$', '', response.strip(), flags=re.MULTILINE)
                    response = response.strip()
                    
                    # Extract only the invoice_preview JSON if multiple JSON objects exist
                    preview_start = response.find('{"type": "invoice_preview"')
                    if preview_start != -1:
                        response = response[preview_start:]
            except Exception as e:
                print(f"Admin agent error: {e}")
                response = f"I received your message: '{message}'. I'm a finance assistant ready to help with payments, invoices, and Salesforce data. (Note: AI model temporarily unavailable)"
            await websocket.send_text(response)
    except WebSocketDisconnect:
        print(f"Admin session closed: {session_id}")

@app.websocket("/ws/user")
async def user_websocket(websocket: WebSocket):
    await websocket.accept()
    
    # Generate unique session ID for this WebSocket connection
    session_id = f"user-{uuid.uuid4()}"
    agent = create_orchestrator_agent(session_id)
    
    print(f"User session started: {session_id}")
    
    try:
        while True:
            message = await websocket.receive_text()
            try:
                response = str(agent(message))
                # Clean invoice preview responses - extract everything after </thinking>
                if '"type": "invoice_preview"' in response:
                    thinking_end = response.find('</thinking>')
                    if thinking_end != -1:
                        response = response[thinking_end + len('</thinking>'):].strip()
                    
                    # Remove markdown code blocks
                    response = re.sub(r'^```json\s*|\s*```$', '', response.strip(), flags=re.MULTILINE)
                    response = response.strip()
                    
                    # Extract only the invoice_preview JSON if multiple JSON objects exist
                    preview_start = response.find('{"type": "invoice_preview"')
                    if preview_start != -1:
                        response = response[preview_start:]
            except Exception as e:
                print(f"User agent error: {e}")
                response = f"Error exception: '{message}'. "
            await websocket.send_text(response)
    except WebSocketDisconnect:
        print(f"User session closed: {session_id}")

@app.post("/api/webhook/payment/success")
async def payment_success_webhook(request: Request):
    data = await request.json()
    print(f"Received payment success webhook: {data}")
    
    
    # Update Salesforce opportunity status
    try:
        from tools import salesforceAgent
        sf_query = f"Update opportunity status to 'Closed Won' and description to 'Payment received' for payment: {json.dumps(data)}"
        sf_result = salesforceAgent(sf_query)
        print(f"Salesforce update result: {sf_result}")
    except Exception as e:
        print(f"Salesforce update failed: {e}")
    
    return {"status": "success"}

@app.post("/api/webhook/payment/fail")
async def payment_fail_webhook(request: Request):
    data = await request.json()
    print(f"Received payment fail webhook: {data}")
    
    # Send SNS notification for payment failure
    try:
        message = f"Payment Failed: {json.dumps(data, indent=2)}"
        sns_client.publish(
            TopicArn=TOPIC_ARN,
            Message=message,
            Subject="Payment Failure Alert"
        )
        print("SNS notification sent for payment failure")
    except Exception as e:
        print(f"SNS notification failed: {e}")
    
    return {"status": "success"}


@app.get("/api/webhook/whatsapp")
async def whatsapp_verify(request: Request):
    """WhatsApp webhook verification"""
    params = request.query_params
    verify_token = "hackathon-hackgoldship"  # Match the token WhatsApp is sending
    
    if params.get("hub.verify_token") == verify_token:
        return int(params.get("hub.challenge", 0))
    return {"error": "Invalid verify token"}

@app.post("/api/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """WhatsApp message webhook handler"""
    data = await request.json()
    print(f"WhatsApp webhook: {data}")
    
    try:
        # Extract message from WhatsApp webhook
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        
        # Ignore status updates, only process incoming messages
        if "statuses" in value:
            return {"status": "success"}
            
        messages = value.get("messages", [])
        
        if messages:
            message = messages[0]
            from_number = message.get("from")
            message_id = message.get("id")
            text = message.get("text", {}).get("body", "")
            
            # Skip if already processed
            if message_id in processed_messages:
                return {"status": "success"}
            
            # Mark as processed
            processed_messages.add(message_id)
            
            # Show typing indicator
            await send_whatsapp_typing(from_number, message_id)
            
            # Send to agent
            from agents import create_orchestrator_agent
            session_id = f"whatsapp-{from_number}-{uuid.uuid4()}"
            agent = create_orchestrator_agent(session_id)
            response = str(agent(text))
            
            # Send response back to WhatsApp
            await send_whatsapp_message(from_number, response)
            
    except Exception as e:
        print(f"WhatsApp webhook error: {e}")
    
    return {"status": "success"}

async def send_whatsapp_typing(to_number: str, message_id: str):
    """Send typing indicator to WhatsApp"""
    import httpx
    
    url = f"https://graph.facebook.com/v18.0/712795175245429/messages"
    headers = {
        "Authorization": "Bearer EAAK43Fk95CUBPUk25teXj0s8T12Y7x8QTyP68gTDy6jsNvVGFxrrPnkvvUujNhKIsFOwTepirLe1xZCWdyslI0hxLiMdsOL2vzxZA8IOkKVgoQrYYsMu7PsZBkTTbGG0ji3HvJERTSi9rol1SpxIA2UcZB8weaCx1m1x64fJTgwBqqbCcSeozX5XcopPc0pw4lZArMICQiHtzIICKz5Vqtux60aNdSFYoqrv9XGcgwDx52wZDZD",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
        "typing_indicator": {
            "type": "text"
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, headers=headers)
    except Exception as e:
        print(f"WhatsApp typing error: {e}")

async def send_whatsapp_message(to_number: str, message: str):
    """Send message back to WhatsApp"""
    import httpx
    
    url = f"https://graph.facebook.com/v18.0/712795175245429/messages"
    headers = {
        "Authorization": "Bearer EAAK43Fk95CUBPUk25teXj0s8T12Y7x8QTyP68gTDy6jsNvVGFxrrPnkvvUujNhKIsFOwTepirLe1xZCWdyslI0hxLiMdsOL2vzxZA8IOkKVgoQrYYsMu7PsZBkTTbGG0ji3HvJERTSi9rol1SpxIA2UcZB8weaCx1m1x64fJTgwBqqbCcSeozX5XcopPc0pw4lZArMICQiHtzIICKz5Vqtux60aNdSFYoqrv9XGcgwDx52wZDZD",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "text": {"body": message}
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            print(f"WhatsApp send response: {response.status_code}")
    except Exception as e:
        print(f"WhatsApp send error: {e}")

@app.get("/api/opportunities/closed")
async def get_closed_opportunities():
    """Get closed opportunities from Salesforce API"""
    try:
        import requests
        import os
        
        # Salesforce credentials - replace with your actual values
        SF_USERNAME = 
        SF_PASSWORD = 
        SF_SECURITY_TOKEN = "Pr3GWeSxORs5YmMYIS22CmCot"
        SF_DOMAIN = "customer-velocity-7923"
        
        # Get access token
        auth_url = f"https://{SF_DOMAIN}.salesforce.com/services/oauth2/token"
        auth_data = {
            'grant_type': 'password',
            'client_id': os.getenv('SF_CLIENT_ID', 'your_client_id'),
            'client_secret': os.getenv('SF_CLIENT_SECRET', 'your_client_secret'),
            'username': SF_USERNAME,
            'password': SF_PASSWORD + SF_SECURITY_TOKEN
        }
        
        auth_response = requests.post(auth_url, data=auth_data)
        auth_json = auth_response.json()
        
        access_token = auth_json['access_token']
        instance_url = auth_json['instance_url']
        
        # Query closed opportunities
        query = "SELECT Name, CloseDate, StageName FROM Opportunity WHERE IsClosed = true ORDER BY CloseDate DESC LIMIT 10"
        query_url = f"{instance_url}/services/data/v58.0/query"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(query_url, headers=headers, params={'q': query})
        data = response.json()
        
        opportunities = []
        if 'records' in data:
            for record in data['records']:
                opportunities.append({
                    'opportunity_name': record['Name'],
                    'date': record['CloseDate'],
                    'status': record['StageName']
                })
        
        return {'opportunities': opportunities}
        
except Exception as e:
        # Return mock data on error
        return {
            'opportunities': [
                {
                    "opportunity_name": "Cloud Transformation Project",
                    "date": "2025-09-15",
                    "status": "Pending"
                },
                {
                    "opportunity_name": "AI Analytics Deployment",
                    "date": "2025-09-18",
                    "status": "Processing"
                },
                {
                    "opportunity_name": "Digital Retail Upgrade",
                    "date": "2025-09-20",
                    "status": "Success"
                },
                {
                    "opportunity_name": "E-Commerce Expansion",
                    "date": "2025-09-21",
                    "status": "Fail"
                },
                {
                    "opportunity_name": "Smart Manufacturing Pilot",
                    "date": "2025-09-22",
                    "status": "Pending"
                },
                {
                    "opportunity_name": "Automation",
                    "date": "2025-09-21",
                    "status": "Overdue"
                }
            ]
        }

@app.get("/api/invoices/overdue-recurring")
async def get_overdue_recurring_invoices():
    """Get overdue recurring invoices for Auto Renew Subscriptions"""
    try:
        import boto3
        from datetime import datetime, timedelta
        
        dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-5')
        table = dynamodb.Table('hackathon-invoice')
        
        # Scan for recurring invoices with overdue status
        response = table.scan(
            FilterExpression='invoice_type = :type AND #status = :status',
            ExpressionAttributeValues={
                ':type': 'recurring',
                ':status': 'overdue'
            },
            ExpressionAttributeNames={'#status': 'status'}
        )
        
        invoices = response.get('Items', [])
        
        # Calculate overdue days for each invoice and filter > 3 days
        current_date = datetime.now()
        filtered_invoices = []
        
        for invoice in invoices:
            created_at = datetime.fromisoformat(invoice['created_at'].replace('Z', '+00:00'))
            # Overdue days = current date - (created date + 7 days)
            due_date = created_at.replace(tzinfo=None) + timedelta(days=7)
            overdue_days = (current_date - due_date).days
            
            # Only include invoices overdue more than 3 days
            if overdue_days > 3:
                invoice['overdue_days'] = overdue_days
                filtered_invoices.append(invoice)
        
        return {'invoices': filtered_invoices}
        
    except Exception as e:
        return {'error': str(e)}

@app.get("/api/dashboard/invoices")
async def get_invoice_dashboard():
    """Get invoice dashboard statistics"""
    try:
        import boto3
        from decimal import Decimal
        from datetime import datetime, date
        
        dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-5')
        table = dynamodb.Table('hackathon-invoice')
        
        # Get today's date
        today = date.today().isoformat()
        
        # Scan all invoices
        response = table.scan()
        invoices = response.get('Items', [])
        
        # Initialize counters
        stats = {
            'pending': {'count': 0, 'amount': 0},
            'processing': {'count': 0, 'amount': 0}, 
            'success': {'count': 0, 'amount': 0},
            'fail': {'count': 0, 'amount': 0},
            'overdue': {'count': 0, 'amount': 0}
        }
        
        today_revenue = 0
        
        # Calculate statistics
        for invoice in invoices:
            status = invoice.get('status', 'pending')
            amount = float(invoice.get('amount', 0))
            created_at = invoice.get('created_at', '')
            
            # Check if invoice was created today
            if created_at.startswith(today):
                if status == 'success':
                    today_revenue += amount
            
            if status in stats:
                stats[status]['count'] += 1
                stats[status]['amount'] += amount
        
        return {
            'today_revenue': today_revenue,
            'invoice_stats': stats
        }
        
    except Exception as e:
        return {'error': str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
