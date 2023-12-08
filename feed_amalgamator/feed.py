"""Code for handling the main, feed page via flask"""
import configparser
import logging
from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import exc

from feed_amalgamator.helpers.custom_exceptions import MastodonConnError
from feed_amalgamator.helpers.logging_helper import LoggingHelper
from feed_amalgamator.helpers.mastodon_data_interface import MastodonDataInterface
from feed_amalgamator.helpers.mastodon_oauth_interface import MastodonOAuthInterface
from feed_amalgamator.helpers.db_interface import dbi, UserServer
from . import CONFIG


bp = Blueprint("feed", __name__, url_prefix="/feed")
parser = configparser.ConfigParser()
# Setting up the loggers and interface layers
with open(CONFIG.path) as file:
    parser.read_file(file)
log_file_loc = Path(parser["LOG_SETTINGS"]["feed_log_loc"])
logger = LoggingHelper.generate_logger(logging.INFO, log_file_loc, "feed_page")
auth_api = MastodonOAuthInterface(logger)
data_api = MastodonDataInterface(logger)

# TODO - Add Swagger/OpenAPI documentation
# TODO - Standardize how exceptions are raised and parsed throughout flask
# TODO - Business logic of home feed (deciding what to filter etc.)

# Defining constants
POSTS_PER_TIMELINE = CONFIG.posts  # Better in a configuration file? Or hard code?
HOME_TIMELINE_NAME = CONFIG.home_timeline
USER_DOMAIN_FIELD = CONFIG.user_domain
LOGIN_TOKEN_FIELD = CONFIG.login_token
USER_ID_FIELD = CONFIG.user_id


def filter_sort_feed(timelines: list[dict]) -> list[dict]:
    """
    Function that sorts and fiters the timeline
    @param timelines : timeline data to need to be filtered and sorted
    """
    for post in timelines:
        for delete in CONFIG.filter_list:
            post.pop(delete)

    return sorted(timelines, key=lambda x: x[CONFIG.sort_by], reverse=True)


@bp.route("/home", methods=["GET"])
def feed_home():
    if request.method == "GET":
        provided_user_id = session[USER_ID_FIELD]
        user_servers = dbi.session.execute(dbi.select(UserServer).filter_by(user_id=provided_user_id)).all()
        if user_servers is None:
            flash("Invalid User")  # issue with hard coded error messages - see below
            logger.error("No user servers found that are tied to user id {i}".format(i=provided_user_id))
            raise Exception  # TODO: We need to standardize how exceptions are raised and parsed in flask.
        else:
            logger.info("Found {n} servers tied to user id {i}".format(n=len(user_servers), i=provided_user_id))
            timelines = []
            for user_server_tuple in user_servers:
                # user_servers is a list of tuples. The object is the first element of the tuple
                user_server = user_server_tuple[0]
                # These are user_server objects defined in the data interface. Treat them like python objects
                server_domain = user_server.server
                access_token = user_server.token
                data_api.start_user_api_client(user_domain=server_domain, user_access_token=access_token)

                timeline = data_api.get_timeline_data(HOME_TIMELINE_NAME, POSTS_PER_TIMELINE)
                # Add server it was retrieved from to be accessed by frontend
                for post in timeline:
                    post["original_server"] = server_domain
                timelines.extend(timeline)
            timelines = filter_sort_feed(timelines)
            return render_template("feed/home.html", timelines=timelines)

    return render_template("feed/home.html", timelines=None)  # Default return


@bp.route("/add_server", methods=["GET", "POST"])
def add_server():
    """Endpoint for the user to add a server to their existing list"""
    if request.method == "POST":
        if USER_DOMAIN_FIELD in request.form:
            return render_redirect_url_page()
        elif LOGIN_TOKEN_FIELD in request.form:
            return render_input_auth_code_page()
    return render_template("feed/add_server.html", is_domain_set=False)


def render_redirect_url_page():
    """Helper function to handle the logic for redirecting users to the Mastodon OAuth flow
    Should inherit the request and session of add_server"""

    domain = request.form[USER_DOMAIN_FIELD]
    logger.info("Rendering redirect url for user inputted domain {d}".format(d=domain))
    session[USER_DOMAIN_FIELD] = domain

    is_valid_domain, parsed_domain = auth_api.verify_user_provided_domain(domain)

    if not is_valid_domain:
        logger.error(
            "User inputted domain {d} was not a valid mastodon domain." "Failed to render redirect url page".format(d=domain)
        )
        raise Exception  # TODO: We will need to standardize how to handle exceptions in the flask context.

    app_token_obj = auth_api.check_if_domain_exists_in_database(parsed_domain)
    if app_token_obj is not None:
        client_id = app_token_obj.client_id
        client_secret = app_token_obj.client_secret
        access_token = app_token_obj.access_token
    else:
        client_id, client_secret, access_token = auth_api.add_domain_to_database(parsed_domain)
        if client_id is None:
            logger.error("Domain {d} did not return a proper API response when adding it" "to the database".format(d=domain))
            return render_template("feed/add_server.html", is_domain_set=False, error=True)
        logger.info("New domain added to the database")

    auth_api.start_app_api_client(parsed_domain, client_id, client_secret, access_token)
    url = auth_api.generate_redirect_url()
    logger.info("Generated redirect url: {u}".format(u=url))
    return render_template("feed/add_server.html", url=url, is_domain_set=True)


def render_input_auth_code_page():
    """Helper function to handle the logic for allowing users to input the auth code.
    Should inherit the request and session of add_server"""
    auth_token = request.form[LOGIN_TOKEN_FIELD]
    user_id = session[USER_ID_FIELD]
    domain = session[USER_DOMAIN_FIELD]

    error = generate_auth_code_error_message(auth_token, user_id, domain)
    if error is None:
        try:
            # The auth_token input by the user is a one-time token used to generate the actual login token
            # Once the auth_token is used, it cannot be reused. We need to save the actual login token
            access_token = auth_api.generate_user_access_token(auth_token)

            user_server_obj = UserServer(user_id=user_id, server=domain, token=access_token)
            dbi.session.add(user_server_obj)
            dbi.session.commit()
        except exc.IntegrityError:
            error = "Record already exists."  # Hardcore error messages, or abstract further?
        except MastodonConnError:
            error = "Error: Could not generate valid login token"
        else:
            # Executes if there is no exception
            return redirect(url_for("feed.add_server", is_domain_set=False))
    flash(error)


def generate_auth_code_error_message(
    authentication_token: str | None, user_id: str | None, user_domain: str | None
) -> str | None:
    """
    Helper function to generate different error messages that will be shown to the user depending
    on what went wrong
    @param authentication_token: auth_token field in the request form
    @param user_id: user_id field in the session
    @param user_domain: user_domain field in the session
    @return: Either the error message, or None
    """
    error = None
    # Hardcode error messages, or abstract further? For localization. If shown to user, will have to localize further
    if not authentication_token:
        error = "Authorization Token in Required"
    elif not user_id:
        error = "Password is required."
    elif not user_domain:
        error = "Domain is required"
    return error


def render_user_servers():
    user_id = session[USER_ID_FIELD]
    user_servers = UserServer.query.filter_by(user_id=user_id).all()
    if len(user_servers) == 0:
        user_servers = None
    return render_template("feed/delete_server.html", user_servers=user_servers)


@bp.route("/delete_server", methods=["GET", "POST"])
def delete_server():
    """Endpoint for the user to delete one or more servers from their existing list"""
    if request.method == "POST":
        user_id = session[USER_ID_FIELD]
        servers = request.form.getlist("servers")
        for server in servers:
            server = UserServer.query.filter_by(user_id=user_id, server=server).first()
            if server:
                dbi.session.delete(server)
                dbi.session.commit()
                logger.info("Deleted server {} of user {}".format(server.server, server.user_id))
            else:
                logger.info("Invalid record for server {} of user {}".format(server.server, server.user_id))
                flash("Invalid record for server {}".format(server))
                raise Exception  # TODO: We will need to standardize how to handle exceptions in the flask context.
            return render_user_servers()

    else:
        return render_user_servers()
