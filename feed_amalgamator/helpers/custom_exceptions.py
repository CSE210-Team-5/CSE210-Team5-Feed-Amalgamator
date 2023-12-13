""""Custom exception class is used instead of the third-party MastdonAPIError in order to insulate
internal code from breaking third party API changes"""


class InvalidApiInputError(Exception):
    """
    Custom exception class for errors encountered when communicating with the Mastodon API.
    In general, thrown if a provided input to the api (eg. a user token or a redirect uri) is invalid
    """

    def __init__(self, error_message: str):
        super().__init__(error_message)


class MastodonConnError(Exception):
    """
    Custom exception class for errors encountered when communicating with the Mastodon API.
    In general, thrown after several repeated tries have failed.
    """

    def __init__(self, error_message: str):
        super().__init__(error_message)


class InvalidDomainError(Exception):
    code = 404
    description = "Invalid Domain"


class InvalidCredentialsError(Exception):
    code = 403
    description = "Forbidden Request"


class NoContentFoundError(Exception):
    code = 400
    description = "Bad Request"


class ServiceUnavailableError(Exception):
    code = 503
    description = "Service Unavailable"


class IntegrityError(Exception):
    code = 500
    description = "Database Integrity Error"
