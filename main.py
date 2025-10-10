from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from typing import Optional
from tool import send_email,received_emails
load_dotenv()
tools=[send_email,received_emails]
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

class EmailContent(BaseModel):
    content: str = Field(description="Generated email content")


def generate(state: dict):
    print("\n=== Generating Email ===")
    cls = state.get("classification")
    
    # Extract recipient name from email
    recipient_name = cls.to.split("@")[0] if cls.to and "@" in cls.to else "there"
    
    # Check if content needs to be generated or is already provided
    if cls.content and len(cls.content.strip()) > 0:
        # Content already provided by user
        email_content = cls.content
        print(f"Using provided content: {email_content}")
    else:
        # Generate content using LLM
        prompt = f"""
        You are an email content generation assistant.
        Generate a professional and friendly email content based on the following:
        
        Recipient: {recipient_name}
        Subject: {cls.subject}
        
        Guidelines:
        - Keep it concise and professional
        - Match the tone to the subject matter
        - Include a proper greeting and closing
        - Make it natural and personalized
        
        Generate only the email body content, nothing else.
        """
        
        structured_llm = llm_model.with_structured_output(EmailContent)
        result = structured_llm.invoke(prompt)
        email_content = result.content
        print(f"Generated content: {email_content}")
    
    print(f"To: {cls.to}")
    print(f"Subject: {cls.subject}")
    print(f"Message: {email_content}")
    

    return {
        "result": "Email prepared successfully",
        "email_details": {
            "to": cls.to,
            "subject": cls.subject,
            "message": email_content
        }
    }
    # print(f"To: {cls.to}")
    # print(f"Subject: {cls.subject}")
    # print(f"Content: {cls.content}")


    
    # Uncomment to actually send:
    # from tool import send_email
    # result = send_email(to=cls.to, subject=cls.subject, body=cls.content)



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
def tool_calling(state):
    print("\n=== Tool Calling ===")
    
    email_details = state.get("email_details", {})
    to = email_details.get("to")
    subject = email_details.get("subject")
    message = email_details.get("message")
    
    print(f"Preparing to send email:")
    print(f"  To: {to}")
    print(f"  Subject: {subject}")
    print(f"  Message: {message}")
    
    prompt = f"""
    Send an email with the following details:
    - To: {to}
    - Subject: {subject}
    - Message: {message}
    
    Use the send_email tool to send this email.
    """
    
    llm_tools = llm_model.bind_tools(tools=tools)
    res = llm_tools.invoke(prompt)
    
    print(f"\nTool calls detected: {res.tool_calls}")
    
    if res.tool_calls:
        for tool_call in res.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            print(f"\nExecuting tool: {tool_name}")
            print(f"Arguments: {tool_args}")
            
            # Find and execute the matching tool
            tool_executed = False
            for tool in tools:
                if tool.name == tool_name:
                    try:
                        result = tool.invoke(tool_args)
                        print(f"Tool execution result: {result}")
                        return {
                            "result": "Email sent successfully",
                            "tool_result": result,
                            "email_details": email_details
                        }
                    except Exception as e:
                        print(f"Error executing tool: {e}")
                        return {
                            "result": f"Error sending email: {str(e)}",
                            "error": str(e)
                        }
            
            if not tool_executed:
                print(f"Warning: Tool '{tool_name}' not found in available tools")
                return {
                    "result": f"Tool '{tool_name}' not found",
                    "error": "Tool not available"
                }
    else:
        print("No tool calls made by the model")
        return {
            "result": "No tool execution needed",
            "response": res.content
        }
# Build the graph
email_state_graph = StateGraph(dict)

email_state_graph.add_node("classify_email_request", classify_email_request)
email_state_graph.add_node("generate", generate)
email_state_graph.add_node("fetch", fetch)
email_state_graph.add_node("handle_not_email", handle_not_email)
email_state_graph.add_node("tool_calling",tool_calling)
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

email_state_graph.add_edge("generate", 'tool_calling')
email_state_graph.add_edge("tool_calling",END)
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

# print("\n" + "=" * 60)
# print("TEST 2: Check Emails")
# print("=" * 60)
# res2 = chat_graph.invoke({
#     "user_request": "show me my unread emails"
# })
# print("\n=== Final Result ===")
# print(res2)