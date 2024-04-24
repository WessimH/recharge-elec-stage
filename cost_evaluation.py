import matplotlib.pyplot as plt


def calculate_aws_costs(ec2_hours_per_day=24, number_of_ec2_instances=6, ec2_instance_type='t3.micro',
                        use_nat_gateway=True, nat_gateway_hours_per_day=5, s3_storage_gb=10,
                        data_out_gb=1, number_of_ip_rotations_per_day=5):
    """
    Calculate the AWS costs for running a scraping operation with micro instances.

    Parameters:
    ec2_hours_per_day (int): Number of hours each EC2 instance runs per day.
    number_of_ec2_instances (int): Total number of EC2 instances.
    ec2_instance_type (str): Type of EC2 instance (assumed all are t3.micro for simplicity).
    use_nat_gateway (bool): Whether a NAT Gateway is used.
    nat_gateway_hours_per_day (int): Number of hours the NAT Gateway is operational per day.
    s3_storage_gb (int): Amount of data stored in S3 in GB.
    data_out_gb (int): Amount of data transferred out of S3 in GB.
    number_of_ip_rotations_per_day (int): Number of times IPs are rotated via NAT Gateway per day.

    Returns:
    float: Total weekly cost.
    """
    # Pricing information (based on AWS pricing as of the last update; needs to be kept current)
    ec2_price_per_hour = 0.0116 if ec2_instance_type == 't3.micro' else 0.0134  # example for 't3.micro'
    nat_gateway_price_per_hour = 0.045
    nat_gateway_data_processing_per_gb = 0.045
    s3_price_per_gb_per_month = 0.023
    s3_data_out_price_per_gb = 0.09

    # EC2 costs

    daily_ec2_cost = ec2_hours_per_day * ec2_price_per_hour * number_of_ec2_instances
    weekly_ec2_cost = daily_ec2_cost * 7

    # NAT Gateway costs
    weekly_nat_gateway_cost = 0
    weekly_nat_data_processing_cost = 0
    if use_nat_gateway:
        weekly_nat_gateway_cost = nat_gateway_hours_per_day * nat_gateway_price_per_hour * 7
        # Estimate data processed per IP rotation; assuming 1 GB processed per rotation for simplicity
        weekly_nat_data_processing_cost = number_of_ip_rotations_per_day * nat_gateway_data_processing_per_gb * 7

    # S3 costs
    monthly_s3_storage_cost = s3_storage_gb * s3_price_per_gb_per_month
    weekly_s3_storage_cost = monthly_s3_storage_cost / 4  # approximate weekly cost
    weekly_s3_data_out_cost = data_out_gb * s3_data_out_price_per_gb

    # Total costs
    total_weekly_cost = (weekly_ec2_cost + weekly_nat_gateway_cost +
                         weekly_nat_data_processing_cost + weekly_s3_storage_cost +
                         weekly_s3_data_out_cost)

    return total_weekly_cost


# Function to plot the evolution of total weekly cost as a function of the number of EC2 instances
print("Calculating costs...")
print(calculate_aws_costs())