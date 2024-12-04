FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app/Domasna2/architecture:$PYTHONPATH

COPY . /app

ENV FLASK_APP=/app/Domasna2/architecture/data_processing_service/app.py

EXPOSE 5002

CMD ["flask", "run", "--host=0.0.0.0", "--port=5002"]
