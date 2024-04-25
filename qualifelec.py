import requests
import xml.dom.minidom as p
import sqlite3
import pandas as pd
import re
import json


# Database setup
conn = sqlite3.connect('data.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS data (
        name TEXT,
        phone TEXT,
        email TEXT,
        street_number TEXT,
        street_name TEXT,
        postal_code TEXT,
        town_name TEXT
    )
''')

# Constants
API = "https://irve.qualifelec.fr/assets/qualifelec-thotem-irve.kml"
BASE_URL = 'https://irve.qualifelec.fr/api/get-correspondant-informations-thotem.php'
GET_FIRST_POINT_DATA = None

# Normalizing phone number
def normalize_phone_number(phone):
    clean_phone = re.sub(r'\D', '', phone)
    if len(clean_phone) == 9 and not clean_phone.startswith('33'):
        clean_phone = '33' + clean_phone
    elif len(clean_phone) == 10 and clean_phone.startswith('0'):
        clean_phone = '33' + clean_phone[1:]
    return clean_phone

# Data Fetching Class
class FetchData:

    def __init__(self, api, base_url, get_first_point_data=None):
        self.api = api
        self.base_url = base_url
        self.get_first_point_data = get_first_point_data
        self.session = requests.Session()

    def get_all_points(self):
        response = self.session.get(self.api)
        response.raise_for_status()

        doc = p.parseString(response.content)
        points = [x.getAttribute("id").removeprefix("placemark") for x in doc.getElementsByTagName("Placemark")]

        if self.get_first_point_data is not None:
            points = points[:self.get_first_point_data]
        return points

    def get_point_data(self, point_id):
        params = json.dumps({"corresp_id": point_id})
        try:
            response = self.session.post(self.base_url, data=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to retrieve data for point {point_id}: {str(e)}")
            return None

        point_data = response.json()
        if not point_data.get('status'):
            return None

        data = point_data.get('message')
        if not data:
            return None

        address_info = data['correspondant']['address']
        street_with_number, postal_code, town_name = address_info.split(" - ")
        street_number_match = re.match(r"^(\d+)\s+(.*)$", street_with_number)
        if not street_number_match:
            return None

        street_number, street_name = street_number_match.groups()
        normalized_phone = normalize_phone_number(data['correspondant']['phone'])

        structured_data = {
            "name": data['name'],
            "phone": normalized_phone,
            "email": data['correspondant']['email'],
            "street_number": street_number,
            "street_name": street_name,
            "postal_code": postal_code,
            "town_name": town_name,
        }

        return structured_data

    def save_to_database(self, data):
        c.execute('''
            INSERT INTO data VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data["name"],
            data["phone"],
            data["email"],
            data["street_number"],
            data["street_name"],
            data["postal_code"],
            data["town_name"],
        ))
        conn.commit()

    def run(self):
        points = self.get_all_points()
        all_data = []
        for point_id in points:
            point_data = self.get_point_data(point_id)
            if point_data:
                self.save_to_database(point_data)
                all_data.append(point_data)

        return pd.DataFrame(all_data)

# Instantiate and run the FetchData class
fetch_data = FetchData(API, BASE_URL, GET_FIRST_POINT_DATA)
result_df = fetch_data.run()
result_df.to_csv("data.csv", index=False)
print("Data collection and saving complete.")
