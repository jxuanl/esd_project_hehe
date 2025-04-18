FROM python:3-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY ./invokes.py ./recommend_inventory_replenishment.py ./
CMD [ "python", "./recommend_inventory_replenishment.py" ]