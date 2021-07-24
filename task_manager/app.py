from task_manager import app
from . import views
from . import filters
from task_manager.config import Config


def init_app():
    app.config.from_object(Config)
    return app
