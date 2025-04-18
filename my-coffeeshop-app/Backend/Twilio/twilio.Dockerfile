# Use Python 3.11 image
FROM python:3.11-slim
WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app.py .
CMD ["python", "./app.py"]

