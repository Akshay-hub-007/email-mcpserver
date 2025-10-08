from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from IPython.display import Image
from tool import send_email, received_emails
from typing import Optional

load_dotenv()

llm_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
email_tools = [send_email, received_emails]
llm_with_tools = llm_model.bind_tools(tools=email_tools)


class EmailClassification(BaseModel):
    classify: str
    status: Optional[str] = None
    context: dict 
# def classify_email_request(user_request: str):
#     print(user_request)
#     prompt = f"""
#     You are an intelligent email classification assistant.
#     Your task is to analyze the user request and classify it for email operations.

#     Follow these rules:
#     1. Determine if the request is related to emails.
#        - If unrelated, respond with:
#          - classify: "NOT_EMAIL"
#          - status: None
#          - context: empty dict

#     2. If the request is related to emails, classify the operation type:
#        - "EMAIL_SEND": User wants to send an email.
#        - "EMAILS_CHECK": User wants to retrieve or read emails.

#     3. For "EMAILS_CHECK", identify the filter/status:
#        - Valid filters: ALL, SEEN, UNSEEN, ANSWERED, UNANSWERED, FLAGGED, UNFLAGGED,
#          DRAFT, DELETED, NEW, OLD, RECENT,
#          FROM "email@example.com", TO "email@example.com", SUBJECT "keyword",
#          BODY "keyword", SINCE DD-MMM-YYYY, BEFORE DD-MMM-YYYY
#        - Default to UNSEEN if not specified.
#        - Put the filter in the "status" field

#     4. For "EMAIL_SEND", extract information from the user request:
#        - "to": recipient email address (REQUIRED)
#        - "subject": email subject (infer if not explicitly mentioned)
#        - "content": email body content
#        - Store these in the "context" dict
       
#        Example for "send email to john@example.com about meeting: Don't forget our meeting at 10 AM":
#          classify: "EMAIL_SEND"
#          status: None
#          context: {{
#              "to": "john@example.com",
#              "subject": "Meeting",
#              "content": "Don't forget our meeting at 10 AM."
#          }}

#     5. Extract ALL relevant information from the user request. Be thorough in parsing the email details.

#     User request: "{user_request}"
    
#     Respond with a properly structured EmailClassification object.
#     """

#     structured_llm = llm_model.with_structured_output(EmailClassification)
#     classification_result = structured_llm.invoke(prompt)
#     return {"classification": classification_result}

def classify_email_request(user_request: str):
    print(user_request)
    prompt = f"""
    You are an intelligent email classification assistant.
    Your task is to analyze the user request and classify it for email operations.

    Follow these rules:
    1. Determine if the request is related to emails.
       - If unrelated, respond with:
         - classify: "NOT_EMAIL"
         - status: None
         - context: empty dict

    2. If the request is related to emails, classify the operation type:
       - "EMAIL_SEND": User wants to send an email.
       - "EMAILS_CHECK": User wants to retrieve or read emails.

    3. For "EMAILS_CHECK", identify the filter/status:
       - Valid filters: ALL, SEEN, UNSEEN, ANSWERED, UNANSWERED, FLAGGED, UNFLAGGED,
         DRAFT, DELETED, NEW, OLD, RECENT,
         FROM "email@example.com", TO "email@example.com", SUBJECT "keyword",
         BODY "keyword", SINCE DD-MMM-YYYY, BEFORE DD-MMM-YYYY
       - Default to UNSEEN if not specified.
       - Put the filter in the "status" field

    4. For "EMAIL_SEND", extract information from the user request:
       - "to": recipient email address (REQUIRED)
       - "subject": email subject (infer if not explicitly mentioned)
       - "content": email body content
       - Store these in the "context" dict
       
       Example for "send email to john@example.com about meeting: Don't forget our meeting at 10 AM":
         classify: "EMAIL_SEND"
         status: None
         context: {{
             "to": "john@example.com",
             "subject": "Meeting",
             "content": "Don't forget our meeting at 10 AM."
         }}

    5. Extract ALL relevant information from the user request. Be thorough in parsing the email details.

    User request: "{user_request}"
    
    Respond with a properly structured EmailClassification object.
    """

    structured_llm = llm_model.with_structured_output(EmailClassification)
    classification_result = structured_llm.invoke(prompt)
    print(classification_result)
    return {"classification": classification_result}

def check_email(classification: dict):
    cls = classification.get("classification").classify
    if cls == "EMAIL_SEND":
        return "generate"
    elif cls == "EMAILS_CHECK":
        return "fetch"
    else:
        return None


def generate(classification: dict):

    pass


def fetch(classification: dict):
    pass


email_state_graph = StateGraph(dict)

email_state_graph.add_node("classify_email_request", classify_email_request)
email_state_graph.add_node("generate", generate)
email_state_graph.add_node("fetch", fetch)

email_state_graph.add_edge(START, "classify_email_request")

email_state_graph.add_conditional_edges(
    "classify_email_request",
    check_email,
    {"generate": "generate", "fetch": "fetch"}
)

email_state_graph.add_edge("generate", END)
email_state_graph.add_edge("fetch", END)

chat_graph = email_state_graph.compile()
res=chat_graph.invoke({
        "user_request": "send an email to akshaykalangi54@gmail.com with subject 'Happy Birthday' and message 'Wishing you a wonderful birthday!'"
})

print(res)