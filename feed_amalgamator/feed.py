"""Code for handling the main, feed page via flask"""
import configparser
import logging
from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import exc

from feed_amalgamator.constants.common_constants import CONFIG_LOC, FILTER_LIST, USER_ID_FIELD, HOME_TIMELINE_NAME, \
    NUM_POSTS_TO_GET, USER_DOMAIN_FIELD, SORT_BY, SERVERS_FIELD, ORIGINAL_SERVER_FIELD
from feed_amalgamator.helpers.custom_exceptions import (
    MastodonConnError, NoContentFoundError, InvalidDomainError, IntegrityError, ServiceUnavailableError,
    InvalidCredentialsError, InvalidApiInputError)
from feed_amalgamator.helpers.logging_helper import LoggingHelper
from feed_amalgamator.helpers.mastodon_data_interface import MastodonDataInterface
from feed_amalgamator.helpers.mastodon_oauth_interface import MastodonOAuthInterface
from feed_amalgamator.helpers.db_interface import dbi, UserServer
from feed_amalgamator.constants.error_messages import NO_CONTENT_FOUND_MSG, USER_SERVER_COMBI_ALREADY_EXISTS_MSG, \
    LOGIN_TOKEN_ERROR_MSG, AUTHORIZATION_TOKEN_REQUIRED_MSG, PASSWORD_REQUIRED_MSG, DOMAIN_REQUIRED_MSG, \
    INVALID_DELETE_SERVER_RECORD_MSG, AUTH_CODE_ERROR_MSG

bp = Blueprint("feed", __name__, url_prefix="/feed")
parser = configparser.ConfigParser()
# Setting up the loggers and interface layers
with open(CONFIG_LOC) as file:
    parser.read_file(file)
log_file_loc = Path(parser["LOG_SETTINGS"]["feed_log_loc"])
redirect_uri = parser["REDIRECT_URI"]["REDIRECT_URI"]
logger = LoggingHelper.generate_logger(logging.INFO, log_file_loc, "feed_page")
auth_api = MastodonOAuthInterface(logger, redirect_uri)
data_api = MastodonDataInterface(logger)

# TODO - Add Swagger/OpenAPI documentation
# TODO - Business logic of home feed (deciding what to filter etc.)


def filter_sort_feed(timelines: list[dict]) -> list[dict]:
    """
    Function that sorts and fiters the timeline
    @param timelines : timeline data to need to be filtered and sorted
    """
    for post in timelines:
        for delete in FILTER_LIST:
            post.pop(delete)

    return sorted(timelines, key=lambda x: x[SORT_BY], reverse=True)


@bp.route("/home", methods=["GET"])
def feed_home():
    if request.method == "GET":
        provided_user_id = session.get(USER_ID_FIELD)
        if provided_user_id is None:
            return redirect(url_for("auth.login"))

        user_servers = UserServer.query.filter_by(user_id=provided_user_id).all()
        if len(user_servers) == 0:
            raise NoContentFoundError({"redirect_path": "feed/home.html",
                                       "message": NO_CONTENT_FOUND_MSG})
        else:
            logger.info("Found {n} servers tied to user id {i}".format(n=len(user_servers), i=provided_user_id))
            timelines = []
            for user_server in user_servers:
                # These are user_server objects defined in the data interface. Treat them like python objects
                server_domain = user_server.server
                access_token = user_server.token
                data_api.start_user_api_client(user_domain=server_domain, user_access_token=access_token)

                timeline = data_api.get_timeline_data(HOME_TIMELINE_NAME, NUM_POSTS_TO_GET)
                # Add server it was retrieved from to be accessed by frontend
                for post in timeline:
                    post[ORIGINAL_SERVER_FIELD] = server_domain
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
    return render_template("feed/add_server.html", is_domain_set=False)


def render_redirect_url_page():
    """Helper function to handle the logic for redirecting users to the Mastodon OAuth flow
    Should inherit the request and session of add_server"""

    domain = request.form[USER_DOMAIN_FIELD]
    logger.info("Rendering redirect url for user inputted domain {d}".format(d=domain))
    session[USER_DOMAIN_FIELD] = domain

    is_valid_domain, parsed_domain = auth_api.verify_user_provided_domain(domain)

    if not is_valid_domain:
        error_message = parsed_domain  # If verify fails, error is returned in place of the domain
        raise InvalidDomainError({
            "redirect_path": "feed/add_server.html",
            "message": error_message})

    app_token_obj = auth_api.check_if_domain_exists_in_database(parsed_domain)
    if app_token_obj is not None:
        logger.info("App token for domain found in database")
        client_id = app_token_obj.client_id
        client_secret = app_token_obj.client_secret
        access_token = app_token_obj.access_token
    else:
        client_id, client_secret, access_token = auth_api.add_domain_to_database(parsed_domain)
        logger.info("New domain added to the database")

    auth_api.start_app_api_client(parsed_domain, client_id, client_secret, access_token)
    url = auth_api.generate_redirect_url()
    logger.info("Generated redirect url: {u}".format(u=url))
    return redirect(url)


def process_provided_auth_token(auth_token):
    """Helper function to handle the logic for allowing users to input the auth code.
    Should inherit the request and session of add_server"""
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
            raise IntegrityError({"redirect_path": "feed/add_server.html",
                                  "message": USER_SERVER_COMBI_ALREADY_EXISTS_MSG})
        except MastodonConnError:
            raise ServiceUnavailableError({"redirect_path": "feed/add_server.html",
                                           "message": LOGIN_TOKEN_ERROR_MSG})
        except InvalidApiInputError:
            raise InvalidCredentialsError({"redirect_path": "feed/add_server.html",
                                           "message": AUTH_CODE_ERROR_MSG})
        else:
            # Executes if there is no exception
            return redirect(url_for("feed.add_server", is_domain_set=False))

    else:
        raise InvalidCredentialsError({
            {"redirect_path": "feed/add_server.html", "message": error}
        })


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
        error = AUTHORIZATION_TOKEN_REQUIRED_MSG
    elif not user_id:
        error = PASSWORD_REQUIRED_MSG
    elif not user_domain:
        error = DOMAIN_REQUIRED_MSG
    return error


@bp.route("/handle_oauth", methods=["GET"])
def handle_oauth():
    """Endpoint for the user to add a server to their existing list"""
    process_provided_auth_token(request.args.get('code'))
    flash('Server added Successfully!!')
    return redirect("/feed/add_server")


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
        servers = request.form.getlist(SERVERS_FIELD)

        for server in servers:
            server = UserServer.query.filter_by(user_id=user_id, server=server).first()
            if server:
                dbi.session.delete(server)
                dbi.session.commit()
                logger.info("Deleted server {} of user {}".format(server.server, server.user_id))
            else:
                invalid_record_msg = "{base}. Server: {s}".format(base=INVALID_DELETE_SERVER_RECORD_MSG, s=server)
                raise IntegrityError({
                    "redirect_path": "feed/delete_server.html",
                    "message": invalid_record_msg
                })
        return render_user_servers()

    else:
        return render_user_servers()
