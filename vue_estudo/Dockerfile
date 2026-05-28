# Use uma imagem base do Python
FROM python:3.13

# Configura o diretório de trabalho
WORKDIR /app

# Copia os arquivos de requisitos e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código para o contêiner
COPY . .
RUN chmod +x /app/entrypoint.sh

# Comando para iniciar o servidor Django
CMD ["/app/entrypoint.sh"]
#CMD exec python manage.py runserver 0.0.0.0:$PORT
#RUN pip install gunicorn

#CMD ["sh", "-c", "gunicorn core.wsgi:application --bind 0.0.0.0:$PORT"]
