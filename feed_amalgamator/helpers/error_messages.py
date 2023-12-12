"""Centralized class for error messages.
By abstracting the error messages like this, localization becomes much simpler in the future.
It also makes code easier to maintain and test - if the string changes, we only need to change it
in one place (as opposed to, say, in both the function and the test for it)"""

USER_ALREADY_EXISTS_MSG = "User already exists. Please Log in to continue"
INVALID_USERNAME_MSG = "Invalid user. Please try again."
INVALID_PASSWORD_MSG = "Invalid Password. Please try again."
NO_CONTENT_FOUND_MSG = "No Mastodon servers exist. Please add one or more servers to view your feed"
USER_SERVER_COMBI_ALREADY_EXISTS_MSG = "This particular combination of User and Server already exists"
LOGIN_TOKEN_ERROR_MSG = "Could not generate valid login token"
AUTHORIZATION_TOKEN_REQUIRED_MSG = "Authorization Token is Required"
PASSWORD_REQUIRED_MSG = "Password is required."
DOMAIN_REQUIRED_MSG = "Domain is required"
INVALID_DELETE_SERVER_RECORD_MSG = "Invalid record for server and user:"
