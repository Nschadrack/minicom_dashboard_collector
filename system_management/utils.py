import random
import string
import csv
import os
import traceback
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings
from .models import AdministrativeUnit, IndustrialZone
from background_task import background
from industry.utils import get_base_domain


def generate_random_code(length=10):
    # Define the characters: lowercase, uppercase letters, and digits
    characters = string.ascii_letters + string.digits
    
    # Generate a random string of the specified length
    random_code = ''.join(random.choice(characters) for _ in range(length))
    
    return random_code

@background()
def bulk_saving_zoning():
    with open(os.path.join(os.getcwd(), "zoning.csv")) as filestream:
        zones = []
        try:
            lines = csv.reader(filestream)
            counts = 0
            for line in lines:
                counts += 1
                name = line[0]
                zone = IndustrialZone.objects.filter(name=name).first()
                if zone is None:
                    zone = IndustrialZone(name=name)
                    zone.save()
                    zones.append(zone)

            print(f"Processed {counts} zonings data instances")
            print("\nBackground task completed\n")
        except Exception as e:
            for zon in zones:
                zon.delete()
            print(f"\n[ERROR]: {str(e)}: Data rolled back\n")
    

@background()
def bulk_saving_administrative():
    try:
        provinces = AdministrativeUnit.objects.filter(category="PROVINCE")
        districts = AdministrativeUnit.objects.filter(category="DISTRICT")
        sectors = AdministrativeUnit.objects.filter(category="SECTOR")
        cells = AdministrativeUnit.objects.filter(category="CELL")
        villages = AdministrativeUnit.objects.filter(category="VILLAGE")
        villages.delete()
        cells.delete()
        sectors.delete()
        districts.delete()
        provinces.delete()

        with open(os.path.join(os.getcwd(), "province_district_sector_cell_village_rwanda.csv"), "r", encoding="utf-8-sig") as filestream:

            data = csv.reader(filestream)
            count = 0
            for line in data:
                count += 1
                province_name, district_name, sector_name, cell_name, village_name = line
                if "kigali" in province_name.lower():
                    province_name = "Kigali city"
                if "burasirazuba" in province_name.lower():
                    province_name = "Eastern"
                if "burengerazuba" in province_name.lower():
                    province_name = "Western"
                if "ruguru" in province_name.lower():
                    province_name = "Northern"
                if "jyepfo" in province_name.lower():
                    province_name = "Southern"

                province = AdministrativeUnit.objects.filter(name=province_name, category="PROVINCE").first()
                if province is None:
                    province = AdministrativeUnit(name=province_name, category="PROVINCE", parent=None)
                    province.save()
                
                district = AdministrativeUnit.objects.filter(name=district_name, category="DISTRICT", parent=province).first()
                if district is None:
                    district = AdministrativeUnit(name=district_name, category="DISTRICT", parent=province)
                    district.save()

                sector = AdministrativeUnit.objects.filter(name=sector_name, category="SECTOR", parent=district).first()
                if sector is None:
                    sector = AdministrativeUnit(name=sector_name, category="SECTOR", parent=district)
                    sector.save()
                
                cell = AdministrativeUnit.objects.filter(name=cell_name, category="CELL", parent=sector).first()
                if cell is None:
                    cell = AdministrativeUnit(name=cell_name, category="CELL", parent=sector)
                    cell.save()

                village = AdministrativeUnit.objects.filter(name=village_name, category="VILLAGE", parent=cell).first()
                if village is None:
                    village = AdministrativeUnit(name=village_name, category="VILLAGE", parent=cell)
                    village.save()

            print(f"Processed { count } data instances")
    except Exception as e:
        print(traceback.format_exc())
        provinces = AdministrativeUnit.objects.filter(category="PROVINCE")
        districts = AdministrativeUnit.objects.filter(category="DISTRICT")
        sectors = AdministrativeUnit.objects.filter(category="SECTOR")
        cells = AdministrativeUnit.objects.filter(category="CELL")
        villages = AdministrativeUnit.objects.filter(category="VILLAGE")
        villages.delete()
        cells.delete()
        sectors.delete()
        districts.delete()
        provinces.delete()
        print(f"{str(e)}\nData have been rolled back\n")


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
                        <p>Platform link: %s</p>
                        <p>You will need some system permissions to start using the system</p>
                        <p>If you have any question, don't hesitate to contact the system administrator for support</p>
    
                        <p style="font-weight:bold;">Regards,<br/>MINICOM Systems Admin Team</p>   
                    </div>
                </div>
            </body>
            </html>
            ''' % (user.get_full_name(), user.email, password, get_base_domain(return_domain_name=True))


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