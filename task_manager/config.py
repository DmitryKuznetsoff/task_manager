import os


class Config(object):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_URI = f'sqlite:////{BASE_DIR}.db'
    DEBUG = True
    SECRET_KEY = os.getenv('SECRET_KY', 'something really secret')
    TIMEZONE = 'UTC'
