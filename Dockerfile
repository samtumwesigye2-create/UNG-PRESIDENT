FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ung_president.py .
COPY password_reset.py .
EXPOSE 8000
CMD ["python", "password_reset.py"]
