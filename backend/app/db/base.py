"""
db/base.py
=============
Declarative base class shared by every ORM model in db/models/.

Keeping this in its own tiny module (rather than defining it inline in
session.py or a models file) avoids circular imports: models import `Base`
from here, Alembic's env.py imports `Base.metadata` from here, and
session.py never needs to import the models package directly.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    pass
