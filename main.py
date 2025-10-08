import email
import imaplib
# from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from langgraph.graph import StateGraph ,START ,END
import tool
load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
tools=[]
try:
    from tool import send_email, received_emails
    tools = [send_email, received_emails]
except Exception:
    tools = []

llm_with_tools=llm.bind_tools(tools=tools)


def check_request(user_request: str):

    prompt="""

        You are classification assisstant for email based on the user request

        if the request is not belong to email......
        

        user request:{user_request}

"""


graph=StateGraph()

graph.add_node('check_request',check_request)

graph.add_node('call_tool', call_tool)