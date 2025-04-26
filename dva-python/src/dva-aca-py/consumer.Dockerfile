FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
COPY static/ ./static/

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "aca_py_controller:app", "--host", "0.0.0.0", "--port", "8052", "--reload"]
