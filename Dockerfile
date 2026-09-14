FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libsndfile1 libopenblas0 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install -e .

RUN mkdir -p /data
ENV BRAINY_DATA_DIR=/data

EXPOSE 8000

CMD ["uvicorn", "brainy.interfaces.api:app", "--host", "0.0.0.0", "--port", "8000"]