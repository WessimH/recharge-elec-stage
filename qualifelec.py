import json
import re
import xml.dom.minidom as p

import boto3
import pandas as pd
import requests
from botocore.exceptions import ClientError
from termcolor import colored

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-2', endpoint_url='http://localhost:8000')

# Constants
API = "https://irve.qualifelec.fr/assets/qualifelec-thotem-irve.kml"
BASE_URL = 'https://irve.qualifelec.fr/api/get-correspondant-informations-thotem.php'
GET_FIRST_POINT_DATA = None


def normalize_phone_number(phone):
    """
    Normalizes a phone number to a standard format.

    Args:
        phone (str): The phone number to normalize.

    Returns:
        str: The normalized phone number.
    """
    clean_phone = re.sub(r'\D', '', phone)
    if len(clean_phone) == 9 and not clean_phone.startswith('33'):
        clean_phone = '33' + clean_phone
    elif len(clean_phone) == 10 and clean_phone.startswith('0'):
        clean_phone = '33' + clean_phone[1:]
    return clean_phone


class FetchData:
    """
    A class used to fetch data from an API and save it to a DynamoDB table.

    ...

    Attributes
    ----------
    api : str
        The URL of the API to fetch data from.
    base_url : str
        The base URL of the API.
    get_first_point_data : int, optional
        The number of points to fetch data for (default is None, which means fetch data for all points).
    session : requests.Session
        The session used to send HTTP requests.

    Methods
    -------
    get_all_points():
        Retrieves all points from the API.
    get_point_data(point_id):
        Retrieves data for a specific point from the API.
    save_to_database(data):
        Saves the provided data to a DynamoDB table.
    run():
        Fetches data for all points and saves it to a DynamoDB table.
    """

    def __init__(self, api, base_url, get_first_point_data=None):
        """
        Constructs all the necessary attributes for the FetchData object.

        Args:
            api (str): The URL of the API to fetch data from.
            base_url (str): The base URL of the API.
            get_first_point_data (int, optional): The number of points to fetch data for (default is None, which means fetch data for all points).
        """
        self.api = api
        self.base_url = base_url
        self.get_first_point_data = get_first_point_data
        self.session = requests.Session()

    def get_all_points(self):
        """
        Retrieves all points from the API.

        Returns:
            list: A list of all points.
        """
        try:
            response = self.session.get(self.api)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(colored(f"Failed to retrieve all points: {str(e)}", 'red'))
            return []

        doc = p.parseString(response.content)
        points = [x.getAttribute("id").removeprefix("placemark") for x in doc.getElementsByTagName("Placemark")]

        if self.get_first_point_data is not None:
            points = points[:self.get_first_point_data]
        return points

    def get_point_data(self, point_id):
        """
        Retrieves data for a specific point from the API.

        Args:
            point_id (str): The ID of the point to fetch data for.

        Returns:
            dict: A dictionary containing the fetched data.
        """
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
        """
        Saves the provided data to a DynamoDB table.

        Args:
            data (dict): The data to save.
        """
        table = dynamodb.Table('Contacts')
        try:
            table.put_item(
                Item={
                    'name': data["name"],
                    'phone': data["phone"],
                    'email': data["email"],
                    'street_number': data["street_number"],
                    'street_name': data["street_name"],
                    'postal_code': data["postal_code"],
                    'town_name': data["town_name"],
                },
                ConditionExpression='attribute_not_exists(phone)'  # Ensure the phone number does not already exist
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print(colored(f"Item with phone {data['phone']} already exists.", 'yellow'))
            else:
                raise

    def run(self):
        """
        Fetches data for all points and saves it to a DynamoDB table.

        Returns:
            pandas.DataFrame: A DataFrame containing all the fetched data.
        """
        points = self.get_all_points()
        print(f"Total number of points: {len(points)}")  # Print the total number of points
        all_data = []
        for point_id in points:
            try:
                point_data = self.get_point_data(point_id)
                # print the data that being inserted in the database
                print(point_data)
                if point_data:
                    self.save_to_database(point_data)
                    all_data.append(point_data)
            except Exception as e:
                print(colored(f"Failed to process point {point_id}: {str(e)}", 'red'))

        return pd.DataFrame(all_data)


# Instantiate and run the FetchData class
fetch_data = FetchData(API, BASE_URL, GET_FIRST_POINT_DATA)
result_df = fetch_data.run()
