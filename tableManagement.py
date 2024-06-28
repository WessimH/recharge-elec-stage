import boto3

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-2', endpoint_url='http://localhost:8000')

# Create the DynamoDB table
try:
    table = dynamodb.create_table(
        TableName='Contacts',
        KeySchema=[
            {
                'AttributeName': 'name',
                'KeyType': 'HASH'  # Partition key
            },
            {
                'AttributeName': 'email',
                'KeyType': 'RANGE'  # Sort key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'name',
                'AttributeType': 'S'  # String type
            },
            {
                'AttributeName': 'phone',
                'AttributeType': 'S'  # String type
            },
            {
                'AttributeName': 'email',
                'AttributeType': 'S'  # String type
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        },
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'PhoneIndex',
                'KeySchema': [
                    {
                        'AttributeName': 'phone',
                        'KeyType': 'HASH'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'  # You can choose KEYS_ONLY or INCLUDE for specific attributes
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            }
        ]
    )
    # Wait until the table is created
    table.meta.client.get_waiter('table_exists').wait(TableName='Contacts')
    print("Table 'Contacts' has been created successfully.")
except dynamodb.meta.client.exceptions.ResourceInUseException:
    # The table already exists
    table = dynamodb.Table('Contacts')
    print("Table 'Contacts' already exists.")
