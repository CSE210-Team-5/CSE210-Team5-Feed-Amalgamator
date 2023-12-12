import logging
import configparser
from pathlib import Path

from flask import (
    Blueprint,
    render_template,
)


from feed_amalgamator.helpers.logging_helper import LoggingHelper

from . import CONFIG

bp = Blueprint("about", __name__)

# Setup for logging and interface layers

# Setting up the loggers and interface layers
parser = configparser.ConfigParser()
with open(CONFIG.path) as file:
    parser.read_file(file)
log_file_loc = Path(parser["LOG_SETTINGS"]["auth_log_loc"])
logger = LoggingHelper.generate_logger(logging.INFO, log_file_loc, "auth_page")
error = ""

# Constants for form fields

# Problem: We need to inject the database layer instead of just calling it like that to make testing easier


@bp.route("/about", methods=["GET"])
def about():
    return render_template("about/about.html")