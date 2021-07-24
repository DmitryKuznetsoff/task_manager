FROM python:3.7.11-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ Europe/Moscow

RUN pip install --upgrade pip

WORKDIR /usr/src/app
COPY . /usr/src/app

RUN pip install -r requirements.txt

EXPOSE 5000

RUN alembic revision --autogenerate
RUN alembic upgrade head
CMD ["python", "run.py"]