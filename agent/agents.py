from strands import Agent
from strands.models import BedrockModel as StrandsBedrockModel
from strands.session.s3_session_manager import S3SessionManager
from strands_tools import retrieve
from tools import salesforceAgent, orchestratedInvoice, sendSNSEmail, reminderAgent, getSalesforceDetails, approveAndSendInvoice, updateInvoiceDatabase
from prompts import ORCHESTRATOR_AGENT_PROMPT
from config import MODEL_ID

model = StrandsBedrockModel(model_id=MODEL_ID, streaming=True)

def create_orchestrator_agent(session_id: str) -> Agent:
    """Create orchestrator agent with unique session ID"""
    session_manager = S3SessionManager(
        session_id=session_id,
        bucket="hackathon-session-context-great-ai-hackathon-2",
        prefix="production/",
        region_name="ap-southeast-5"
    )
    
    return Agent(
        system_prompt=ORCHESTRATOR_AGENT_PROMPT,
        tools=[salesforceAgent, getSalesforceDetails, orchestratedInvoice, approveAndSendInvoice, sendSNSEmail, reminderAgent, retrieve, updateInvoiceDatabase],
        session_manager=session_manager,
        model=model
    )