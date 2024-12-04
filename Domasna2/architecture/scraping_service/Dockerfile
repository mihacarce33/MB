FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app/Domasna2/architecture:$PYTHONPATH

COPY . /app

ENV FLASK_APP=/app/Domasna2/architecture/scraping_service/app.py

EXPOSE 5001

CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]
