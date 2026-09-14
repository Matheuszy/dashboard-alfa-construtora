FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8050

# Usa o Gunicorn (servidor de produção) rodando com 2 trabalhadores (workers)
# "dash_app:server" aponta para o arquivo dash_app.py e a variável 'server' do Flask
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "2", "dash_app:server"]