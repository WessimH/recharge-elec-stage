import boto3

# Initialize a DynamoDB client
dynamodb_client = boto3.client('dynamodb', region_name='us-east-2', endpoint_url='http://localhost:8000')

# List all tables
response = dynamodb_client.list_tables()
tables = response['TableNames']

# Print the names of all tables
print("Available tables:")
for table in tables:
    print(table)
