import functools
import logging
import configparser
from pathlib import Path

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from feed_amalgamator.helpers.db_interface import dbi, User

from feed_amalgamator.helpers.logging_helper import LoggingHelper

from werkzeug.security import check_password_hash, generate_password_hash

from sqlalchemy import exc

bp = Blueprint("auth", __name__, url_prefix="/auth")

# Setup for logging and interface layers

# Setting up the loggers and interface layers
CONFIG_FILE_LOC = Path("configuration/app_settings.ini")  # Path is hardcoded, needs to be changed
parser = configparser.ConfigParser()
parser.read(CONFIG_FILE_LOC)
log_file_loc = Path(parser["LOG_SETTINGS"]["feed_log_loc"])
logger = LoggingHelper.generate_logger(logging.INFO, log_file_loc, "feed_page")
error = ""
print(parser.sections())

@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        try:
            user = User(username=username, password=password)
            dbi.session.add(user)
            dbi.session.commit()
        except exc.IntegrityError:
            pass  # Hardcore error messages, or abstract further?
        else:
            # Executes if there is no exception
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("Invalid User")  # issue with hard coded error messages - see below
            logger.error("No such user found")
            raise Exception  # TODO: We need to standardize how exceptions are raised and parsed in flask.
        elif not check_password_hash(user.password, password):
            flash("Invalid Password")  # issue with hard coded error messages - see below
            logger.error(f"Invalid Password for user {username}")
            raise Exception  # TODO: We need to standardize how exceptions are raised and parsed in flask.
        else:
            session.clear()
            session["user_id"] = user.user_id
            return redirect(url_for("feed.feed_home"))

        flash(error)

    return render_template("auth/login.html")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = dbi.session.execute(dbi.select(User).filter_by(user_id=user_id)).one()


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.register"))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view
