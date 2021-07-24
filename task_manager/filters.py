from task_manager import app
from utils import utc_to_local


@app.template_filter()
def local_datetime(dt):
    return utc_to_local(dt)
