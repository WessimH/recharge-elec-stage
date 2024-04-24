import json
import pandas as pd
import re
import requests
import time
import xml.dom.minidom as p

# Constants
GET_FIRST_POINT_DATA = None  # Set to None to fetch all points
API = "https://irve.qualifelec.fr/assets/qualifelec-thotem-irve.kml"
BASE_URL = 'https://irve.qualifelec.fr/api/get-correspondant-informations-thotem.php'
df = pd.DataFrame()


def normalize_phone_number(phone):
    # Remove non-numeric characters and spaces
    clean_phone = re.sub(r'\D', '', phone)
    # Assuming French phone numbers without country code, prepend with '33' if not already present
    if len(clean_phone) == 9 and not clean_phone.startswith('33'):
        clean_phone = '33' + clean_phone
    elif len(clean_phone) == 10 and clean_phone.startswith('0'):
        clean_phone = '33' + clean_phone[1:]
    return clean_phone


# break this down into smaller functions

class FetchData:
    def __init__(self, api, base_url, get_first_point_data=None):
        self.api = api
        self.base_url = base_url
        self.get_first_point_data = get_first_point_data
        self.data = {}
        self.elapsed_time = 0
        self.completed_requests = 0
        self.points = []

    def get_all_points(self):
        response = requests.get(self.api)
        if response.status_code != 200:
            raise Exception("Failed to fetch data from API")

        print("Successfully got the data from the API. Starting to parse the XML.")
        doc = p.parseString(response.content)
        self.points = [x.getAttribute("id").removeprefix("placemark") for x in doc.getElementsByTagName("Placemark")]
        print(doc)
        if self.get_first_point_data is not None:
            self.points = self.points[:self.get_first_point_data]

        print(f"Total points to collect data: {len(self.points)}")
        return self.points

    def get_point_data(self, point_id):
        params = json.dumps({"corresp_id": point_id})
        try:
            response = requests.post(self.base_url, data=params)
            response.raise_for_status()  # This will raise an HTTPError if the response was not successful
        except requests.exceptions.RequestException as e:
            print(f"Failed to retrieve data for point {point_id}: {str(e)}")
            return None

        point_data = response.json()
        if not point_data.get('status'):
            print("Data retrieval unsuccessful.")
            return None

        data = point_data.get('message')
        if not data:
            print("No message data found.")
            return None

        # Parsing the address
        address_info = data['correspondant']['address']
        address_parts = address_info.split(" - ")
        if len(address_parts) != 3:
            print("Address format is incorrect.")
            return None

        street_with_number, postal_code, town_name = address_parts
        street_number_match = re.match(r"^(\d+)\s+(.*)$", street_with_number)
        if not street_number_match:
            print("Street number and name are not in the expected format.")
            return None

        street_number, street_name = street_number_match.groups()

        # Normalize phone number
        normalized_phone = normalize_phone_number(data['correspondant']['phone'])

        # Constructing the structured response
        structured_data = {
            "name": data['name'],
            "phone": normalized_phone,
            "email": data['correspondant']['email'],
            "street_number": street_number,
            "street_name": street_name,
            "postal_code": postal_code,
            "town_name": town_name,
        }

        self.data[point_id] = structured_data  # Storing the structured data
        self.elapsed_time += response.elapsed.total_seconds()
        self.completed_requests += 1
        print(f"Collected structured data for point {point_id}")

        return structured_data


if __name__ == "__main__":
    fetch_data = FetchData(API, BASE_URL, GET_FIRST_POINT_DATA)
    points = fetch_data.get_all_points()
    while True:
        for point_id in points:
            # add fetched data to a dataframe
            point_data = fetch_data.get_point_data(point_id)
            # Append the data to the DataFrame
            if point_data is not None:
                df = pd.concat([df, pd.DataFrame([point_data])], ignore_index=True)
        df.to_csv("data.csv", index=False)
        print("Data saved. Waiting for 30 minutes before the next save.")
        if fetch_data.completed_requests == len(points):
            print("All points have been saved. Stopping the script.")
            break
        time.sleep(1800)  # Wait for 30 minutes
