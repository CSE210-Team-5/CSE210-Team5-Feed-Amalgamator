import os
import configparser
import urllib


from flask import Flask, redirect, url_for

from . import auth, feed, about
from feed_amalgamator.helpers.db_interface import dbi
from feed_amalgamator.helpers import error_handler # noqa
from feed_amalgamator.constants.common_constants import CONFIG_LOC


def create_app(test_config=None, db_file_name=None):
    parser = configparser.ConfigParser()
    # Setting up the loggers and interface layers
    with open(CONFIG_LOC) as file:
        parser.read_file(file)
    # create and configure the app
    environment_type = parser["ENVIRONMENT"]["ENVIRONMENT"]
    secret_key = parser["ENVIRONMENT"]["SECRET_KEY"]
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = secret_key
    db_location = None
    if environment_type == "dev":
        app.config["DATABASE"] = os.path.join(app.instance_path, "flaskr.sqlite")
        try:
            os.makedirs(app.instance_path)
        except OSError:
            pass
        # Default db location
        if db_file_name is None:
            db_location = "sqlite:///{loc}".format(loc=os.path.join(app.instance_path, "flaskr.sqlite"))
        else:
            db_location = "sqlite:///{loc}".format(loc=os.path.join(app.instance_path, db_file_name))
    elif environment_type == "prod":
        connection_string = parser["DATABASE"]["CONNECTION_STRING"]
        uri_prefix = parser["DATABASE"]["URI_PREFIX"]
        params = urllib.parse.quote_plus(connection_string)
        db_location = uri_prefix.format(params)

    app.config['SQLALCHEMY_DATABASE_URI'] = db_location
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    app.register_blueprint(auth.bp)
    app.register_blueprint(feed.bp)
    app.register_blueprint(about.bp)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_location
    dbi.init_app(app)

    @app.route("/", methods=["GET"])
    def redirect_internal():
        return redirect(url_for("feed.feed_home"))

    with app.app_context():
        dbi.create_all()
    return app
