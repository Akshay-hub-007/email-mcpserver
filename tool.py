import smtplib
import imaplib
import email
from langchain_core.tools import tool
from email.message import EmailMessage

# ---------------- Email Configuration ---------------- #
SENDER_EMAIL = "akshaykalangi54@gmail.com"
APP_PASSWORD = "fljg lwry rstg pvgr"  
IMAP_SERVER = "imap.gmail.com"



@tool()
def send_email(receiver_email, subject, message="Hello!"):
    '''sending email tool'''
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 587) as s:
            s.login(SENDER_EMAIL, APP_PASSWORD)
            full_message = f"Subject: {subject}\n\n{message}"
            s.sendmail('akshaykalangi9@gmail.com', receiver_email, full_message)
        print("✅ Email sent successfully!")
    except Exception as e:
        print("❌ Error:", e)
@tool
def received_emails(email_type: str = "UNSEEN"):
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
        conn = imaplib.IMAP4_SSL(IMAP_SERVER)
        conn.login(SENDER_EMAIL, APP_PASSWORD)
        conn.select("INBOX")

        status, data = conn.search(None, email_type)
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

                emails_list.append({
                    "subject": subject,
                    "from": sender,
                    "body": body
                })

        conn.logout()

    except Exception as e:
        print("Error:", e)

    return emails_list

if __name__=="__main__":
    send_email.invoke({"receiver_email": "akshaykalangi54@gmail.com", "subject": "hello", "message": "happy birthday"})
