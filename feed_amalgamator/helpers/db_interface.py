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
    """Class that represents the user table"""

    __tablename__ = "user"
    user_id: Mapped[int] = mapped_column(dbi.Integer, primary_key=True, autoincrement=True, name="id")
    username: Mapped[str] = mapped_column(dbi.String(20), nullable=False, unique=True, name="username")
    password: Mapped[str] = mapped_column(dbi.String(1000), nullable=False, name="password")


class UserServer(dbi.Model):
    """Class that represents the table that stores each users' servers"""

    __tablename__ = "user_server"
    user_server_id: Mapped[int] = mapped_column(dbi.Integer, primary_key=True, autoincrement=True, name="id")
    user_id: Mapped[int] = mapped_column(dbi.Integer, dbi.ForeignKey("user.id"), name="user_id")
    server: Mapped[str] = mapped_column(dbi.String(100), nullable=False, name="server")
    token: Mapped[str] = mapped_column(dbi.String(500), nullable=False, name="token")


class ApplicationTokens(dbi.Model):
    """Class that represents the table for storing data related to clients for various servers"""

    __tablename__ = "application_tokens"
    server_id: Mapped[int] = mapped_column(dbi.Integer, primary_key=True, autoincrement=True, name="id")
    server: Mapped[str] = mapped_column(dbi.String(100), nullable=False, name="server")
    client_id: Mapped[str] = mapped_column(dbi.String(500), nullable=False, name="client_id")
    client_secret: Mapped[str] = mapped_column(dbi.String(500), nullable=False, name="client_secret")
    access_token: Mapped[str] = mapped_column(dbi.String(500), nullable=False, name="access_token")
    redirect_uri: Mapped[str] = mapped_column(dbi.String(500), nullable=False, name="redirect_uri")
