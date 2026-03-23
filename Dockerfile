FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV MCP_TRANSPORT=streamable-http
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "mcp_server.py"]
