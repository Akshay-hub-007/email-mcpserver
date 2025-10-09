from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from typing import Optional

load_dotenv()

llm_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")


class EmailClassification(BaseModel):
    classify: str = Field(description="Classification type: EMAIL_SEND, EMAILS_CHECK, or NOT_EMAIL")
    status: Optional[str] = Field(default=None, description="Email filter status for EMAILS_CHECK operations")
    # Flatten the context fields
    to: Optional[str] = Field(default=None, description="Recipient email address for EMAIL_SEND")
    subject: Optional[str] = Field(default=None, description="Email subject for EMAIL_SEND")
    content: Optional[str] = Field(default=None, description="Email body content for EMAIL_SEND")


def classify_email_request(state: dict):
    user_request = state.get("user_request", "")
    print(f"Processing request: {user_request}")
    
    prompt = f"""
    Analyze this user request and extract email operation details.

    Rules:
    1. Set "classify" to one of: EMAIL_SEND, EMAILS_CHECK, or NOT_EMAIL
    
    2. For EMAIL_SEND requests:
       - Extract "to": the recipient email address
       - Extract "subject": the email subject line
       - Extract "content": the email message body
       - Set "status" to None
    
    3. For EMAILS_CHECK requests:
       - Set "status" to the filter type (UNSEEN, ALL, SEEN, etc.)
       - Set "to", "subject", "content" to None
    
    4. For NOT_EMAIL requests:
       - Set all fields to None except classify

    User request: "{user_request}"
    
    Extract ALL information present in the request.
    """

    structured_llm = llm_model.with_structured_output(EmailClassification)
    classification_result = structured_llm.invoke(prompt)
    print(f"Classification result: {classification_result}")
    
    return {
        "classification": classification_result,
        "user_request": user_request
    }


def check_email(state: dict):
    cls = state.get("classification").classify
    print(f"Routing based on classification: {cls}")
    
    if cls == "EMAIL_SEND":
        return "generate"
    elif cls == "EMAILS_CHECK":
        return "fetch"
    else:
        return "end"


def generate(state: dict):
    print("\n=== Generating Email ===")
    cls = state.get("classification")
    
    if not cls.to:
        print("Error: Missing recipient email address")
        return {"error": "Missing recipient email address"}
    
    print(f"To: {cls.to}")
    print(f"Subject: {cls.subject}")
    print(f"Content: {cls.content}")
    
    # Uncomment to actually send:
    # from tool import send_email
    # result = send_email(to=cls.to, subject=cls.subject, body=cls.content)
    
    return {
        "result": "Email sent successfully",
        "email_details": {
            "to": cls.to,
            "subject": cls.subject,
            "content": cls.content
        }
    }


def fetch(state: dict):
    print("\n=== Fetching Emails ===")
    cls = state.get("classification")
    status = cls.status or "UNSEEN"
    
    print(f"Fetching emails with status: {status}")
    
    # Uncomment to actually fetch:
    # from tool import received_emails
    # result = received_emails(status=status)
    
    return {
        "result": "Emails fetched successfully",
        "status": status
    }


def handle_not_email(state: dict):
    return {"result": "Request is not email-related"}


# Build the graph
email_state_graph = StateGraph(dict)

email_state_graph.add_node("classify_email_request", classify_email_request)
email_state_graph.add_node("generate", generate)
email_state_graph.add_node("fetch", fetch)
email_state_graph.add_node("handle_not_email", handle_not_email)

email_state_graph.add_edge(START, "classify_email_request")

email_state_graph.add_conditional_edges(
    "classify_email_request",
    check_email,
    {
        "generate": "generate",
        "fetch": "fetch",
        "end": "handle_not_email"
    }
)

email_state_graph.add_edge("generate", END)
email_state_graph.add_edge("fetch", END)
email_state_graph.add_edge("handle_not_email", END)

chat_graph = email_state_graph.compile()

# Test cases
print("=" * 60)
print("TEST 1: Send Email")
print("=" * 60)
res = chat_graph.invoke({
    "user_request": "send an email to akshaykalangi54@gmail.com with subject 'Happy Birthday' and message 'Wishing you a wonderful birthday!'"
})
print("\n=== Final Result ===")
print(res)

print("\n" + "=" * 60)
print("TEST 2: Check Emails")
print("=" * 60)
res2 = chat_graph.invoke({
    "user_request": "show me my unread emails"
})
print("\n=== Final Result ===")
print(res2)