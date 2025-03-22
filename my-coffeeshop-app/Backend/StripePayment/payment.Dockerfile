FROM python:3-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY ./create_payment_intent.py .
CMD [ "python", "./create_payment_intent.py" ]
