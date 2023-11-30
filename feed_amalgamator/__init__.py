import os

from flask import Flask, redirect, url_for

from . import auth, db, feed
from feed_amalgamator.helpers.db_interface import dbi


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",  # Probably something that should not be hard coded in plaintext
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(feed.bp)

    # Hard coded db location atm, but we will need to refactor this entire init
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///{loc}".format(loc=os.path.join(app.instance_path, "flaskr.sqlite"))
    dbi.init_app(app)

    @app.route("/", methods=["GET"])
    def redirect_internal():
        return redirect(url_for("auth.register"))

    return app
