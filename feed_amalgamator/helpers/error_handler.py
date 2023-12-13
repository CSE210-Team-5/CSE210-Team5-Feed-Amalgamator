import logging
import configparser
from flask import render_template
from pathlib import Path

from feed_amalgamator.constants.common_constants import CONFIG_LOC
from feed_amalgamator.helpers.custom_exceptions import (
    InvalidCredentialsError, NoContentFoundError, InvalidDomainError,
    ServiceUnavailableError, IntegrityError)
from feed_amalgamator.auth import bp as auth_bp
from feed_amalgamator.feed import bp as feed_bp
from feed_amalgamator.helpers.logging_helper import LoggingHelper

parser = configparser.ConfigParser()
# Setting up the loggers and interface layers
with open(CONFIG_LOC) as file:
    parser.read_file(file)
log_file_loc = Path(parser["LOG_SETTINGS"]["feed_log_loc"])
redirect_uri = parser["REDIRECT_URI"]["REDIRECT_URI"]
feed_logger = LoggingHelper.generate_logger(logging.INFO, log_file_loc, "feed_page")
auth_logger = LoggingHelper.generate_logger(logging.INFO, log_file_loc, "auth_page")


@feed_bp.errorhandler(InvalidDomainError)
@feed_bp.errorhandler(NoContentFoundError)
@feed_bp.errorhandler(ServiceUnavailableError)
@feed_bp.errorhandler(IntegrityError)
def handle_feed_exceptions(err):
    feed_logger.exception(err)
    return render_template(err.args[0]['redirect_path'], error_message=err.args[0]['message'])


@auth_bp.errorhandler(InvalidCredentialsError)
@auth_bp.errorhandler(IntegrityError)
def handle_auth_exceptions(err):
    auth_logger.exception(err)
    return render_template(err.args[0]['redirect_path'], error_message=err.args[0]['message'])
