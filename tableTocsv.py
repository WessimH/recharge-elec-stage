import boto3
import csv

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-2', endpoint_url='http://localhost:8000')

# Scan the table to fetch all items
table = dynamodb.Table('Contacts')  # Replace with your actual table name
items = table.scan()['Items']

# Open a new CSV file in write mode
with open('output.csv', 'w', newline='') as file:
    # Create a CSV writer
    writer = csv.writer(file)

    # Write the header row to the CSV file
    if items:
        header = items[0].keys()
        writer.writerow(header)

        # Iterate over each item
        for item in items:
            # For each item, write a row to the CSV file
            writer.writerow(item.values())