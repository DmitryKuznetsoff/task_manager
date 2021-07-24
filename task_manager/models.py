import enum

from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, Enum, ForeignKey, func


class TaskStatusEnum(enum.Enum):
    active = 'ACTIVE'
    in_progress = 'IN_PROGRESS'
    completed = 'COMPLETED'
    canceled = 'CANCELED'

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


meta = MetaData()

user = Table(
    'user', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('username', String, unique=True, nullable=False),
    Column('pwd_hash', String, nullable=False)
)

task = Table(
    'task', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('title', String, unique=True, nullable=False),
    Column('description', String, nullable=False),
    Column('created_at', DateTime),
    Column('user_id', Integer, ForeignKey('user.id'), default=None)
)

status = Table(
    'status', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('task_id', ForeignKey('task.id')),
    Column('status', Enum(TaskStatusEnum), nullable=False, default=TaskStatusEnum.active),
    Column('updated_at', DateTime, default=func.now(), onupdate=func.now())
)
