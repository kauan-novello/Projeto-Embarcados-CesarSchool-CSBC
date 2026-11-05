FROM python:3.12-slim

WORKDIR /ml

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY data/raw/ ./data/raw/
COPY notebooks/ ./notebooks/

CMD ["python", "src/train.py"]
