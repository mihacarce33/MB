# Use Python 3.9-slim as base image
FROM python:3.9-slim

# Set working directory inside container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files to the container
COPY . .

# Expose the port Flask will run on
EXPOSE 5000

# Command to run Flask app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
