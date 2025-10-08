import smtplib
import os
from langchain_core.tools import tool


SENDER_EMAIL = "akshaykalangi9@gmail.com"
APP_PASSWORD = "nvozzcjnlsliygxi"  
imap_server = "imap.gmail.com"

@tool
def send_email(receiver_email: str, message: str = "Hello!"):
    """Send an email using Gmail SMTP."""
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(SENDER_EMAIL, APP_PASSWORD)
            s.sendmail(SENDER_EMAIL, receiver_email, message)
            print(f"Email sent successfully to {receiver_email}")
    except Exception as e:
        print("Error:", e)

import imaplib
import email
from langchain_core.tools import tool

@tool
def received_emails(type: str = "UNSEEN"):
    """Fetch received emails and return their subject, sender, and body."""

    def extract_email_body(message):
        """Extract plain text body from an email message."""
        body = ""
        if message.is_multipart():
            for part in message.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get("Content-Disposition"))
                if ctype == "text/plain" and "attachment" not in cdispo:
                    body = part.get_payload(decode=True)
                    try:
                        body = body.decode()
                    except Exception:
                        body = body.decode("utf-8", errors="ignore")
                    break
        else:
            body = message.get_payload(decode=True).decode("utf-8", errors="ignore")
        return body

    emails_list = []

    try:
        conn = imaplib.IMAP4_SSL(imap_server)
        conn.login(SENDER_EMAIL, APP_PASSWORD)
        conn.select("INBOX")

        status, data = conn.search(None, type)
        mail_ids = data[0].split()

        if not mail_ids:
            print("No emails found.")
        else:
            for num in mail_ids:
                status, msg_data = conn.fetch(num, "(RFC822)")
                message = email.message_from_bytes(msg_data[0][1])

                subject = message["subject"]
                sender = message["from"]
                body = extract_email_body(message)
                print(body)
                emails_list.append({
                    "subject": subject,
                    "from": sender,
                    "body": body
                })

        conn.logout()

    except Exception as e:
        print("Error:", e)

    return emails_list

if __name__ == "__main__":
    print(received_emails.invoke("SINCE 07-Oct-2025"))