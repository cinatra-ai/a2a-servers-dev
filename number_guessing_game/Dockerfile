FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001 8002 8003
# Compose overrides CMD per service: agent_Alice.py | agent_Bob.py | agent_Carol.py
CMD ["python", "agent_Alice.py"]
