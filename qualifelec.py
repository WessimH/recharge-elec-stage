import json
import re
import xml.dom.minidom as p

import boto3
import pandas as pd
import requests

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-2', endpoint_url='http://localhost:8000')

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
        if not data or 'correspondant' not in data or 'address' not in data['correspondant']:
            print("No address information found in response data.")
            return None

        # Retrieve the address information safely
        address_info = data['correspondant']['address']

        # First, split by " - " to obtain up to three parts
        split_address_info = address_info.split(" - ", 2)
        if len(split_address_info) != 3:
            # If there are not exactly three parts, the address format is invalid assing Invalid address format.
            split_address_info = ["Invalid address format", "Invalid address format", "Invalid address format"]
        # Extract individual parts
        street_with_number = split_address_info[0]
        postal_code = split_address_info[1]
        town_name = split_address_info[2]

        street_number_match = re.match(r"^(\d+)\s+(.*)$", street_with_number)
        if not street_number_match:
            street_number = "Invalid street format"
            street_name = "Invalid street format"
        else:
            street_number, street_name = street_number_match.groups()

        # Normalize the phone number (make sure the `normalize_phone_number` function is defined elsewhere)
        normalized_phone = normalize_phone_number(data['correspondant']['phone'])

        structured_data = {
            "name": data['name'],
            "phone": normalized_phone,
            "email": data['correspondant']['email'],
            "street_number": street_number,
            "street_name": street_name,
            "postal_code": postal_code,
            "town_name": town_name
        }

        return structured_data

    def save_to_database(self, data):
        table = dynamodb.Table('Contacts')
        table.put_item(
            Item={
                'name': data["name"],
                'phone': data["phone"],
                'email': data["email"],
                'street_number': data["street_number"],
                'street_name': data["street_name"],
                'postal_code': data["postal_code"],
                'town_name': data["town_name"],
            }
        )

    def run(self):
        points = self.get_all_points()
        all_data = []
        for point_id in points:
            point_data = self.get_point_data(point_id)
            # print the data that being inserted in the database
            print(point_data)
            if point_data:
                self.save_to_database(point_data)
                all_data.append(point_data)

        return pd.DataFrame(all_data)


# Instantiate and run the FetchData class
fetch_data = FetchData(API, BASE_URL, GET_FIRST_POINT_DATA)
result_df = fetch_data.run()
