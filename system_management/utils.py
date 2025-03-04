import random
import string
from dotenv import load_dotenv
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings


def generate_random_code(length=10):
    # Define the characters: lowercase, uppercase letters, and digits
    characters = string.ascii_letters + string.digits
    
    # Generate a random string of the specified length
    random_code = ''.join(random.choice(characters) for _ in range(length))
    
    return random_code

def send_mails(receiver_email, subject, body):
    try:
        host = settings.EMAIL_HOST
        port = settings.EMAIL_PORT
        login = settings.EMAIL_ID
        password = settings.EMAIL_PASSWORD

        to = f"To: {receiver_email}"
        from_whom = login
        subject = subject
        body = body

        message = MIMEMultipart()
        message["To"] = to
        message["From"] = from_whom
        message["Subject"] = subject
        message["Bcc"] = ""
        message.attach(MIMEText(body, "html"))

        text_to_send = message.as_string()

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as server:
            server.login(login, password)
            server.sendmail(login, to, text_to_send)

        return True  # email was sent
    except Exception as e:
        print(f"\n[ERROR]: while sending email: {str(e)}\n")
        return False  # email was not sent

def build_default_password_email_template(user, password):
    return '''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title></title>
                <style>
                    body {
                        margin: 0;
                        padding: 0;
                        background-color: #ffffff;
                        font-family: arial, sans-serif;
                    }
                    .container {
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 10px;
                        background-color:#ffffff;
                        border-radius: 8px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    }
                    .content {
                        padding: 10px;
                    }
                    .button {
                        display: inline-block;
                        background-color: #ff0000;
                        color: #fff;
                        text-decoration: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        margin: 20px;
                    }
                    .button:hover {
                        background-color: #dd0000;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="content">
                        <p style='font-weight: bold;'>Dear %s,</p><br/>
                        <p>Your account has been created successfully</p>
                        <p>Your account username is <b>%s<b></p>
                        <p>Here is your random generated default password to login, you will be prompted to change your password</p>
                        <p style="text-align: center; background-color: #773377; color: white; padding: 10px; font-weight: bold; margin-bottom:10px;">%s</p>
                        <p>You will need some system permissions to start using the system</p>
                        <p>If you have any question, don't hesitate to contact the system administrator for support</p>
    
                        <p style="font-weight:bold;">Regards,<br/>MINICOM Systems Admin Team</p>   
                    </div>
                </div>
            </body>
            </html>
            ''' % (user.get_full_name(), user.email, password)


def build_default_account_creation_email_template(user, password):
    return '''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title></title>
                <style>
                    body {
                        margin: 0;
                        padding: 0;
                        background-color: #ffffff;
                        font-family: arial, sans-serif;
                    }
                    .container {
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 10px;
                        background-color:#eeccaa;
                        border-radius: 8px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    }
                    .content {
                        padding: 10px;
                    }
                    .button {
                        display: inline-block;
                        background-color: #ff0000;
                        color: #fff;
                        text-decoration: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        margin: 20px;
                    }
                    .button:hover {
                        background-color: #dd0000;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="content">
                        <p style='font-weight: bold;'>Dear %s,</p><br/>
                        <p>Your account has been created successfully</p>
                        <p>Your account username is <b>%s<b></p>
                        <p>You can use your username with your password to login and access the system. You will need some system permissions to start using the system</p>
                        <p>If you have any question, don't hesitate to contact the system administrator for support</p>
                        <p style="font-weight:bold;">Regards,<br/>MINICOM Systems Admin Team</p>   
                    </div>
                </div>
            </body>
            </html>
            ''' % (user.get_full_name(), user.email)