FROM python:3.8-slim
WORKDIR /app

# 1. Copy and install only dependencies (cache-efficient)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 2. Now copy rest of the code
COPY . .

CMD ["python", "app.py"]
