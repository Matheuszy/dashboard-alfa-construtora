FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8050

CMD ["gunicorn", "--chdir", "src", "--bind", "0.0.0.0:8050", "--workers", "2", "dash_app:server"]