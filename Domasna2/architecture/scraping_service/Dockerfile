# Use Python 3.9-slim as base image
FROM python:3.9-slim

# Set working directory inside container
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Set the PYTHONPATH to include shared directories
ENV PYTHONPATH=/app/Domasna2/architecture:$PYTHONPATH

# Copy project files to the container
COPY . /app

# Set the Flask app entry point
ENV FLASK_APP=/app/Domasna2/architecture/scraping_service/app.py

# Expose the port Flask will run on
EXPOSE 5001

# Command to run Flask app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]
