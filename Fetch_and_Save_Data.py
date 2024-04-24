
import pandas as pd
import requests
import json
import xml.dom.minidom as p
import datetime

# Constants
GET_FIRST_POINT_DATA = None # Set to None to fetch all points
API = "https://irve.qualifelec.fr/assets/qualifelec-thotem-irve.kml"
BASE_URL = 'https://irve.qualifelec.fr/api/get-correspondant-informations-thotem.php'

def fetch_data():
    response = requests.get(API)
    if response.status_code != 200:
        raise Exception("Failed to fetch data from API")

    print("Successfully got the data from the API. Starting to parse the XML.")
    doc = p.parseString(response.content)
    points = [x.getAttribute("id").removeprefix("placemark") for x in doc.getElementsByTagName("Placemark")]

    if GET_FIRST_POINT_DATA is not None:
        points = points[:GET_FIRST_POINT_DATA]

    print(f"Total points to collect data: {len(points)}")
    
    # DataFrame to hold all data
    all_data_df = pd.DataFrame()
    
    data = {}
    elapsed_time = 0
    completed_requests = 0

    for point_id in points:
        params = json.dumps({"corresp_id": point_id})
        response = requests.post(BASE_URL, data=params)

        if response.status_code == 200:
            point_data = response.json()
            data[point_id] = point_data
            
            # Process data into DataFrame
            temp_df = pd.json_normalize(point_data)
            temp_df['point_id'] = point_id
            
            # Append data to DataFrame
            all_data_df = pd.concat([all_data_df, temp_df], ignore_index=True)
            print(f"Current DataFrame size: {len(all_data_df)} rows.")
            
            elapsed_time += response.elapsed.total_seconds()
            completed_requests += 1
            remaining_points = len(points) - completed_requests
            estimated_time = datetime.timedelta(seconds=round((remaining_points * (elapsed_time / completed_requests))))
            print(f"Collected data for point {point_id}. Need to collect {remaining_points} more. Est. time: {estimated_time}")
        else:
            print(f"Failed to retrieve data for point {point_id}: {response.status_code}")

    # Save DataFrame to CSV
    all_data_df.to_csv("data.csv", index=False)
    print("Data has been saved to data.csv")

fetch_data()
