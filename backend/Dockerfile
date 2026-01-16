# Build python image
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app
# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Run the application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
EXPOSE 5000