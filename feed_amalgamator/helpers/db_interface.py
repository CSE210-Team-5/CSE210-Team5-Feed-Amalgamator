"""Abstraction layer for connecting to the database.
This allows for easier manipulation of the data. More importantly, it allows the program to work
with any SQL backend, be it PostGRE or MySQl."""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# dbi = db interface
dbi = SQLAlchemy()  # Not initialized without the app


class User(dbi.Model):
    __tablename__ = "user"
    user_id: Mapped[int] = mapped_column(dbi.Integer, primary_key=True, autoincrement=True, name="id")
    username: Mapped[str] = mapped_column(dbi.String, nullable=False, unique=True, name="username")
    password: Mapped[str] = mapped_column(dbi.String, nullable=False, name="password")


class UserServer(dbi.Model):
    __tablename__ = "user_server"
    user_server_id: Mapped[int] = mapped_column(dbi.Integer, primary_key=True, autoincrement=True, name="id")
    user_id: Mapped[int] = mapped_column(dbi.Integer, dbi.ForeignKey("user.id"), name="user_id")
    server: Mapped[str] = mapped_column(dbi.String, nullable=False, name="server")
    """TODO - For future versions of the project. The access token to the third party api is stored as plaintext
    at the moment. Coming up with a solution is not viable for this sprint"""
    token: Mapped[str] = mapped_column(dbi.String, nullable=False, name="token")
