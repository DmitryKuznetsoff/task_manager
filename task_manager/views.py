from datetime import datetime
from functools import reduce

from flask import render_template, request, redirect, url_for, session, abort
from sqlalchemy import select, insert, or_, and_, func

from task_manager.app import app
from task_manager.db import conn, engine
from task_manager.models import task, status, user
from utils import get_password_hash, local_to_utc


@app.get('/login')
def login():
    return render_template('login.html')


@app.get('/logout')
def logout():
    session.pop('user_id')
    session.pop('username')
    return redirect(url_for('login'))


@app.post('/auth')
def auth():
    username = request.form.get('login')
    password = request.form.get('password')
    select_user = select(user).where(and_(user.c.pwd_hash == get_password_hash(password), user.c.username == username))
    authorized_user = conn().execute(select_user).fetchone()
    if not authorized_user:
        return abort(401)
    # set user into session:
    session['user_id'] = authorized_user.id
    session['username'] = authorized_user.username
    return redirect(url_for('active_tasks'))


@app.get('/register')
@app.post('/register')
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        repeat_password = request.form['repeat_password']

        if password != repeat_password:
            abort(400)
        insert_user = insert(user).values(username=username, pwd_hash=get_password_hash(password))
        conn().execute(insert_user)
        return redirect(url_for('login'))
    return render_template('register.html')


@app.get('/')
def index():
    return redirect(url_for('active_tasks'))


@app.get('/active_tasks')
def active_tasks():
    select_tasks = select(task).join(status).where(status.c.status == 'active').order_by(task.c.created_at)
    tasks = conn().execute(select_tasks).fetchall()
    context = {'tasks': tasks}
    return render_template('active_tasks.html', **context)


def check_user_authorized():
    user_id = session.get('user_id')
    if not user_id:
        return abort(401)
    return user_id


@app.post('/take_task/<task_id>')
def take_task(task_id):
    user_id = check_user_authorized()
    with engine().begin() as c:
        update_task = task.update().values(user_id=user_id).where(task.c.id == task_id)
        update_task_status = status.update().values(status='in_progress').where(status.c.task_id == task_id)
        c.execute(update_task)
        c.execute(update_task_status)
    return redirect(url_for('active_tasks'))


@app.get('/create_task')
@app.post('/create_task')
def create_task():
    if request.method == 'POST':
        data = dict(request.form)
        # convert str date and time to datetime object:
        creation_date = data.pop('creation_date')
        creation_time = data.pop('creation_time')
        created_at = datetime.strptime(f'{creation_date} {creation_time}', '%Y-%m-%d %H:%M')
        utc_created_at = local_to_utc(created_at)

        data['created_at'] = utc_created_at
        with engine().begin() as c:
            insert_task = insert(task).values(**data)
            new_task = c.execute(insert_task)
            # insert related status record:
            new_task_id, = new_task.inserted_primary_key
            insert_task_status = insert(status).values(task_id=new_task_id, updated_at=datetime.now())
            c.execute(insert_task_status)
    return render_template('create_task.html')


@app.get('/in_progress')
def in_progress_tasks():
    users_subq = select(user.c.id, user.c.username).subquery()
    status_subq = select(status.c.task_id, status.c.status, status.c.updated_at,
                         func.max(status.c.updated_at).label('maxdate')).group_by(
        status.c.task_id).subquery()

    select_active_tasks = select(task, users_subq.c.username, status_subq.c.updated_at).join(status_subq).where(
        status_subq.c.status == 'in_progress', task.c.user_id == users_subq.c.id)

    tasks = conn().execute(select_active_tasks)
    context = {'tasks': tasks}
    return render_template('in_progress_tasks.html', **context)


@app.post('/complete_task/<task_id>')
def complete_task(task_id):
    check_user_authorized()
    insert_status_completed = insert(status).values(task_id=task_id, status='completed')
    conn().execute(insert_status_completed)
    return redirect(url_for('in_progress_tasks'))


@app.post('/cancel_task/<task_id>')
def cancel_task(task_id):
    check_user_authorized()
    insert_status_canceled = insert(status).values(task_id=task_id, status='canceled')
    conn().execute(insert_status_canceled)
    return redirect(url_for('in_progress_tasks'))


@app.get('/archive')
def archive():
    select_tasks = select(task, status.c.status, status.c.updated_at).join(status).where(
        or_(status.c.status == 'completed', status.c.status == 'canceled'))
    tasks = conn().execute(select_tasks)
    context = {'tasks': tasks}
    return render_template('archive.html', **context)


@app.get('/stats')
def stats():
    in_progress = count_by_status('in_progress')
    active = count_by_status('active')
    canceled = count_by_status('canceled')
    average_execution_time = get_avg_execution_time()

    context = {
        'in_progress': in_progress,
        'active': active,
        'canceled': canceled,
        'average_execution_time': average_execution_time
    }
    return render_template('stats.html', **context)


def count_by_status(task_status: str) -> int:
    subq = select(status.c.id, func.max(status.c.updated_at).label('maxdate')).group_by(
        status.c.task_id).subquery()

    query = select(func.count()).where(status.c.id == subq.c.id, status.c.status == task_status)
    counter, = conn().execute(query).fetchone()
    return counter


def get_avg_execution_time():
    # select completed task ids and time as dict:
    select_completed = select(status.c.task_id, status.c.updated_at).where(status.c.status == 'completed')
    completed = dict(conn().execute(select_completed).fetchall())
    if not completed:
        return 0
    # select task ids and time with 'in_progress' status
    select_in_progress_time = select(status.c.updated_at).where(status.c.id.in_(dict(completed).keys()))
    in_progress_time = conn().execute(select_in_progress_time).fetchall()
    in_progress_time = [t for t, in in_progress_time]
    # calculate overall execution time for all tasks:
    execution_time = [k - v for k, v in dict(zip(completed.values(), in_progress_time)).items()]
    # calculate average execution time by dividing overall execution time on completed tasks amount:
    average_execution_time = reduce(lambda x, y: x + y, execution_time) / len(completed)
    return average_execution_time
