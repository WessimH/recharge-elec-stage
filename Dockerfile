# Use an official Python base image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

# Expose the appropriate port
EXPOSE 80

# Specify the command to run the application
CMD ["python", "app.py"]
