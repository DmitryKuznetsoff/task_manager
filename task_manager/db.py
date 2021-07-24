from sqlalchemy import create_engine

from task_manager import app


def engine():
    return create_engine(app.config['DB_URI'])


def conn():
    return engine().connect()
