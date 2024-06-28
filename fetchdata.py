import sqlite3
import boto3
from botocore.exceptions import ClientError

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
table = dynamodb.Table('Contacts')

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

    # Skip items with empty phone values
    if not item['phone']:
        print(f"Skipping item with empty phone value: {item}")
        continue

    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(phone)'
        )
        print(f"Inserted item: {item}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print(f"Duplicate item found for phone: {item['phone']}. Deleting existing item.")
            # Find the existing item with the same phone
            response = table.query(
                IndexName='PhoneIndex',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('phone').eq(item['phone'])
            )
            if response['Items']:
                existing_item = response['Items'][0]
                # Delete the existing item
                table.delete_item(
                    Key={
                        'name': existing_item['name'],
                        'email': existing_item['email']
                    }
                )
                print(f"Deleted existing item: {existing_item}")
            # Insert the new item
            table.put_item(Item=item)
            print(f"Inserted new item: {item}")
        else:
            raise

# Close the SQLite connection
conn.close()

# Scan and print all items in the Contacts table
response = table.scan()
items = response['Items']

print("\nInserted Items:")
for item in items:
    print(item)
