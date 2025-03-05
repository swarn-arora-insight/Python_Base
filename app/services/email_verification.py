"""
all email that triggered for the user and admin
"""

from pathlib import Path
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from dotenv import load_dotenv
import os
from dotenv import load_dotenv

load_dotenv()
import root_dir_getter 

FROM_EMAIL = os.getenv("FROM_EMAIL")
PASSWORD = os.getenv("PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")

root_dir_getter.set_root_dir(__file__)  # pylint: disable=wrong-import-position

def send_email_verification_mail(user_email: str, first_name: str, authenticate_link: str) -> bool:
    """
    Sends an email verification email to the user using Gmail SMTP.

    Args:
        user_email (str): The user's email address.
        first_name (str): The user's first name.
        authenticate_link (str): The verification link.

    Returns:
        bool: True if email is sent successfully, False otherwise.
    """
    # Email subject
    subject = "Email Verification Request"
    # Load HTML template
    email_content_file_location = Path(
        os.path.join(
            "assets",  # Assuming your HTML file is in the 'assets/html/' directory
            "html",
            "email_verification.html"
        )
    )
    
    try:
        # Read and customize the HTML template
        with open(email_content_file_location, "r", encoding="utf-8") as file:
            html_content = file.read()
        html_content = html_content.replace("{{user}}", first_name)
        html_content = html_content.replace("{{authenticate_link}}", authenticate_link)

        # Create email message
        message = MIMEMultipart()
        message["From"] = FROM_EMAIL
        message["To"] = user_email
        message["Subject"] = subject
        message.attach(MIMEText(html_content, "html"))

        # Connect to Gmail's SMTP server and send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(FROM_EMAIL, PASSWORD)  # Log in with Gmail credentials
            server.send_message(message)  # Send the email
            return True

    except Exception as e:
        return False

