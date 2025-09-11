FROM python:3.11-slim
WORKDIR /app

# 1. Copy only dependency files
COPY requirements.txt pyproject.toml ./

# 2. Copy src so setuptools can see it
COPY src ./src

# 3. Install dependencies + your package
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir setuptools wheel && \
    pip install --no-cache-dir .

# 4. Copy rest (configs, scripts, etc.)
COPY . .

CMD ["python", "app.py"]
