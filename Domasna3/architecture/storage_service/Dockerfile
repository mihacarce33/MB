FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app/Domasna2/architecture:$PYTHONPATH

COPY . /app

ENV FLASK_APP=/app/Domasna2/architecture/storage_service/app.py

EXPOSE 5003

CMD ["flask", "run", "--host=0.0.0.0", "--port=5003"]
