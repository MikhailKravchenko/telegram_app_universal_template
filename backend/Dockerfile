FROM python:3.12

ENV PYTHONUNBUFFERED=1

RUN mkdir /code
WORKDIR /code

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y netcat-traditional
RUN pip install --upgrade pip

# Устанавливаем Python зависимости (включая daphne для ASGI)
COPY requirements.txt /code/requirements.txt
RUN pip install -r requirements.txt


COPY ./runserver.sh /
RUN chmod +x /runserver.sh

EXPOSE 8000

COPY . /code/

COPY ./entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
