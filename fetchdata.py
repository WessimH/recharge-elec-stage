import sqlite3

import boto3

# Connect to SQLite database
conn = sqlite3.connect('./data/data.db')
cursor = conn.cursor()

# Execute a query to fetch data matching the columns shown in the image
cursor.execute("""
    SELECT name, phone, email, street_number, street_name, postal_code, town_name
    FROM data
""")
rows = cursor.fetchall()

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-2', endpoint_url='http://localhost:8000')

# Create the DynamoDB table if it doesn't already exist
try:
    table = dynamodb.create_table(
        TableName='Contacts',
        KeySchema=[
            {
                'AttributeName': 'name',
                'KeyType': 'HASH'  # Partition key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'name',
                'AttributeType': 'S'  # String type
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    # Wait until the table is created
    table.meta.client.get_waiter('table_exists').wait(TableName='Contacts')
    print("Table 'Contacts' has been created successfully.")
except dynamodb.meta.client.exceptions.ResourceInUseException:
    # The table already exists
    table = dynamodb.Table('Contacts')
    print("Table 'Contacts' already exists.")

# Insert data into the DynamoDB table
for row in rows:
    item = {
        'name': row[0],
        'phone': row[1],
        'email': row[2],
        'street_number': row[3],
        'street_name': row[4],
        'postal_code': row[5],
        'town_name': row[6]
    }
    table.put_item(Item=item)

# Close the SQLite connection
conn.close()

# Scan and print all items in the Contacts table
response = table.scan()
items = response['Items']

print("\nInserted Items:")
for item in items:
    print(item)
