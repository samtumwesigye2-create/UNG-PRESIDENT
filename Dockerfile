FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ung_president.py .
COPY password_reset.py .
COPY registration_response_fix.py .
COPY bootstrap.py .
EXPOSE 8000
CMD ["python", "bootstrap.py"]
