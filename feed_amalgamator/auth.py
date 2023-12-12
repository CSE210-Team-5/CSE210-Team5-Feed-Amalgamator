import functools
import logging
import configparser
from pathlib import Path

import sqlalchemy.exc
from flask import (
    Blueprint,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from feed_amalgamator.helpers.custom_exceptions import InvalidCredentialsError, IntegrityError

from feed_amalgamator.helpers.db_interface import dbi, User

from feed_amalgamator.helpers.logging_helper import LoggingHelper

from werkzeug.security import check_password_hash, generate_password_hash

from sqlalchemy import exc

from feed_amalgamator.constants.common_constants import USERNAME_FIELD, PASSWORD_FIELD, USER_ID_FIELD, CONFIG_LOC
from feed_amalgamator.constants.error_messages import USER_ALREADY_EXISTS_MSG, INVALID_USERNAME_MSG, \
    INVALID_PASSWORD_MSG, USER_DOES_NOT_EXIST_MSG

bp = Blueprint("auth", __name__, url_prefix="/auth")

# Setup for logging and interface layers

# Setting up the loggers and interface layers
parser = configparser.ConfigParser()
with open(CONFIG_LOC) as file:
    parser.read_file(file)
log_file_loc = Path(parser["LOG_SETTINGS"]["auth_log_loc"])
logger = LoggingHelper.generate_logger(logging.INFO, log_file_loc, "auth_page")

# Constants for form fields

# Problem: We need to inject the database layer instead of just calling it like that to make testing easier


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form[USERNAME_FIELD]
        password = generate_password_hash(request.form[PASSWORD_FIELD])
        try:
            user = User(username=username, password=password)
            dbi.session.add(user)
            dbi.session.commit()
        except exc.IntegrityError:
            raise IntegrityError(
                {"message": USER_ALREADY_EXISTS_MSG,
                 "redirect_path": "auth/register.html"})
        else:
            # Executes if there is no exception
            return redirect(url_for("auth.login"))
    # Executes if there is an exception
    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form[USERNAME_FIELD]
        password = request.form[PASSWORD_FIELD]
        user = User.query.filter_by(username=username).first()
        if user is None:
            raise InvalidCredentialsError({"message": INVALID_USERNAME_MSG,
                                           "redirect_path": "auth/login.html"})
        elif not check_password_hash(user.password, password):
            raise InvalidCredentialsError({"message": INVALID_PASSWORD_MSG,
                                           "redirect_path": "auth/login.html"})
        else:
            session.clear()
            session[USER_ID_FIELD] = user.user_id
            return redirect(url_for("feed.feed_home"))
    return render_template("auth/login.html")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        try:
            g.user = dbi.session.execute(dbi.select(User).filter_by(user_id=user_id)).one()
        except sqlalchemy.exc.NoResultFound:
            raise IntegrityError(
                {"message": USER_DOES_NOT_EXIST_MSG + ":{u}".format(u=user_id),
                 "redirect_path": "auth/register.html"})



@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view
