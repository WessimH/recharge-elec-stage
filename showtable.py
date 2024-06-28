import boto3

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-2', endpoint_url='http://localhost:8000')

# List all tables
table_list = dynamodb.tables.all()

# Print the names of all tables and their item count
for table in table_list:
    item_count = len(table.scan()['Items'])
    print(f"Table: {table.name}, Item Count: {item_count}")