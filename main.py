import email
import imaplib
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
load_dotenv()
user_email = "akshaykalangi9@gmail.com"
password = "nvozzcjnlsliygxi" 
imap_server = "imap.gmail.com"

client = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

def extract_email_body(message):
    """Extract plain text body from email message"""
    body = ""
    if message.is_multipart():
        for part in message.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get("Content-Disposition"))
            if ctype == "text/plain" and "attachment" not in cdispo:
                body = part.get_payload(decode=True)
                try:
                    body = body.decode()
                except:
                    body = body.decode("utf-8", errors="ignore")
                break
    else:
        body = message.get_payload(decode=True).decode("utf-8", errors="ignore")
    return body

try:
    conn = imaplib.IMAP4_SSL(imap_server)
    conn.login(user_email, password)
    conn.select("INBOX")

    status, data = conn.search(None, "UNSEEN")
    mail_ids = data[0].split()

    if not mail_ids:
        print("No emails found.")
    else:
        # latest_two = mail_ids[-2:]

        for num in mail_ids:
            status, msg_data = conn.fetch(num, "(RFC822)")
            message = email.message_from_bytes(msg_data[0][1])

            subject = message["subject"]
            sender = message["from"]
            body = extract_email_body(message)

            # print(f"Subject: {subject}")
            # print(f"From: {sender}")
            # print("--- Original Body ---")
            # print(body)
            print("\n--- Summary ---")

            user_name = user_email.split("@")[0]
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an intelligent email assistant."),
                ("human", f"Analyze this email for {user_name} and provide a clear, concise summary with key points:\n{{email_body}}")
            ])

            response = client.invoke(prompt.format_messages(email_body=body))
            print(response.content)
            print("\n" + "="*50 + "\n")

    conn.logout()

except Exception as e:
    print("Error:", e)
