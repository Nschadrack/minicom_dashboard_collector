import random
import string
from collections import defaultdict
import csv
import traceback
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings
from .models import AdministrativeUnit, IndustrialZone
from django.db import transaction
from background_task import background


def generate_random_code(length=10):
    # Define the characters: lowercase, uppercase letters, and digits
    characters = string.ascii_letters + string.digits
    
    # Generate a random string of the specified length
    random_code = ''.join(random.choice(characters) for _ in range(length))
    
    return random_code

@background()
def bulk_saving_zoning(filestream):
    try:
        zones = []
        # Save them in bulk
        with transaction.atomic():
            lines = filestream.readlines()
            cache_zones = defaultdict()
            for line in lines:
                name = line.split(",")[0]
                name= name.strip().title()
                zone = cache_zones.get(name, None)
                if zone is None:
                    zone = IndustrialZone(name=name)
                    cache_zones[name] = zone
                    zones.append(zone)

            IndustrialZone.objects.bulk_save(zones)
        print(f"Processed {len(zones)} data instances")
    except Exception as e:
        print(f"\n[ERROR]: {str(e)}: Data rolled back with {len(zones)} records\n")
    

@background()
def bulk_saving_administrative(filestream):
    provinces = []
    districts = []
    sectors = []
    cells = []
    villages = []
    try:
        # Save them in bulk
        with transaction.atomic():
            reader = csv.reader(filestream)
            count = 0  
            objects_cache = defaultdict(dict)
            for row in reader:
                count += 1
                if len(row) != 5:
                    print("\nSkipped the row: {row}\nBecause it has more/less than 5 expected columns")
                    continue
            
                province_name, district_name, sector_name, cell_name, village_name = row
                # Uppercase processing
                province_name = province_name.strip().upper()
                district_name = district_name.strip().upper()
                sector_name = sector_name.strip().upper()
                cell_name = cell_name.strip().upper()
                village_name = village_name.strip().upper()

                province = objects_cache.get(f"province_{province_name}", None)
                if province is None:
                    province = AdministrativeUnit(name=province_name, category="PROVINCE", parent=None)
                    objects_cache[f"province_{province_name}"] = province
                    provinces.append(province)
                
                district = objects_cache.get(f"province_district_{district_name}", None)
                if district is None:
                    district = AdministrativeUnit(name=district_name, category="DISTRICT", parent=province)
                    objects_cache[f"province_district_{district_name}"] = district
                    districts.append(district)

                sector = objects_cache.get(f"province_district_sector_{sector_name}", None)
                if sector is None:
                    sector = AdministrativeUnit( name=sector_name, category="SECTOR", parent=district)
                    objects_cache[f"province_district_sector_{sector_name}"] = sector
                    sectors.append(sector)
                
                cell = objects_cache.get(f"province_district_sector_cell_{cell_name}", None)
                if cell is None:
                    cell = AdministrativeUnit(name=cell_name, category="CELL", parent=sector)
                    objects_cache[f"province_district_sector_cell_{cell_name}"] = cell
                    cells.append(cell)

                village = objects_cache.get(f"province_district_sector_cell_village_{village_name}", None)
                if village is None:
                    village = AdministrativeUnit(name=village_name, category="VILLAGE", parent=cell)
                    objects_cache[f"province_district_sector_cell_village_{village_name}"] = village
                    villages.append(village)
            
            provinces.extend(districts)
            provinces.extend(sectors)
            provinces.extend(cells)
            provinces.extend(villages)

            
            AdministrativeUnit.objects.bulk_save(provinces)

        print(f"Processed {len(provinces)} data instances")
    except Exception as e:
        print(traceback.format_exc())
        print(f"{str(e)}\nData have been rolled back with {len(provinces)} records")

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