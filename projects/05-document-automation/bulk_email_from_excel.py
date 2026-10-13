"""Send one personalised e-mail per row of an Excel sheet (columns: Email, Text).

Credentials come from environment variables, never from the source:
    SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
"""
import os
import smtplib
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd


def connect(server_name: str, port: int, user: str, password: str):
    try:
        server = smtplib.SMTP(server_name, port)
        server.starttls()
        server.login(user, password)
        return server
    except Exception as exc:
        print(f"Failed to connect to the SMTP server: {exc}")
        return None


def send_emails(excel_file: str, subject: str, cc_emails: str = "", delay: float = 2.0) -> None:
    server_name = os.environ["SMTP_SERVER"]
    port = int(os.environ.get("SMTP_PORT", 587))
    user, password = os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"]

    data = pd.read_excel(excel_file)
    if not {"Email", "Text"}.issubset(data.columns):
        sys.exit("The Excel file must contain 'Email' and 'Text' columns.")

    server = connect(server_name, port, user, password)
    if not server:
        return

    for _, row in data.iterrows():
        message = MIMEMultipart()
        message["From"], message["To"], message["Subject"], message["Cc"] = user, row["Email"], subject, cc_emails
        message.attach(MIMEText(row["Text"], "plain"))
        recipients = [row["Email"]] + (cc_emails.split(",") if cc_emails else [])
        try:
            server.sendmail(user, recipients, message.as_string())
            print(f"Sent to {row['Email']}")
        except smtplib.SMTPServerDisconnected:
            print("Server disconnected, reconnecting...")
            server = connect(server_name, port, user, password)
            if not server:
                print(f"Skipping {row['Email']}")
                continue
            server.sendmail(user, recipients, message.as_string())
        except Exception as exc:
            print(f"Failed for {row['Email']}: {exc}")
        time.sleep(delay)  # stay under provider rate limits

    server.quit()


if __name__ == "__main__":
    send_emails("recipients.xlsx", subject="Your results", cc_emails="")
