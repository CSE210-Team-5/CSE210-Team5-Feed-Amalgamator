"""This interface provides an abstraction (ports/adapter model) to insulate internal code from external API changes.

Any module interacting with the Mastodon API for Oauth purposes should do so strictly through this layer"""

import logging
import json
import mastodon.errors
import requests
from urllib.parse import urlparse
from http import HTTPStatus

from mastodon import Mastodon, MastodonAPIError  # pip install Mastodon.py
from feed_amalgamator.helpers.custom_exceptions import (
    MastodonConnError,
    InvalidApiInputError,
)
from feed_amalgamator.helpers.db_interface import dbi, ApplicationTokens

# Add more logging levels (info etc. - forgot about this)
# Segment https error types to become more descriptive
# Need to test the third party api thoroughly (definitely need to sanity check the url)
# Eg. test that data fields that are needed are returned; create a weird fizzborb to create "deterministic" tests


class MastodonOAuthInterface:
    """Adapter Class for responsible for handling the user Oauth chain
    All calls to the API during the user Oauth process should go through this layer to insulate
    code from third party libraries.
    API calls for data processing AFTER Oauth is under the responsibility of MastodonDataInterface
    """

    def __init__(self, logger: logging.Logger):
        """We pass in a logger instead of creating a new one
        As we want logs to be logged to the program calling the interface
        rather than have separate logs for the interface layer specifically"""
        self.logger = logger
        """This is the client used to authenticate users. Generated using our app's down details"""
        self.app_client = None
        """Hard coded required scopes for the app to work. Revisit if the scope changes"""
        self.REQUIRED_SCOPES = ["read", "write", "push"]
        """The redirect URI required by the API to generate certain urls"""
        self.REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"

    # ===== Functions to handle the authorization pipeline with the user =====
    def verify_user_provided_domain(self, user_domain: str) -> (bool, str):
        """
        Ensures that the user provided domain is a legitimate mastodon server
        @param user_domain: Server of the account provided by the user
        @return: True (if server is a legitimate mastodon domain), False otherwise
        """
        wanted_domain = self._clean_user_provided_domain(user_domain)

        # Hardcoded endpoint for generally getting an instance's info
        endpoint_to_test = "https://{d}/api/v2/instance".format(d=wanted_domain)
        # As this is before any api client is created, we will use a simple https request
        try:
            headers = self._generate_headers_for_api_call()
            response = requests.get(endpoint_to_test, headers=headers)
            if response.status_code == HTTPStatus.OK:
                wanted_domain = json.loads(response.content)['domain']
                return True, wanted_domain  # Obtain the cleansed content
        except requests.exceptions.ConnectionError as e:
            # If the user domain is invalid, it is indistinguishable from a connection error (cannot resolve
            # the domain of the redirected url)
            # Increase granularity of http error logging (500?400?)
            self.logger.error(
                "ConnectionError {e} trying to verify user provided domain. User provided domain"
                "is either invalid, or there is a connection problem".format(e=e)
            )
        except json.JSONDecodeError:
            self.logger.error("JsonDecodeError {e}: Response obtained from server while verifying domain was "
                              "successful, but returned a value that cannot be parsed. Server is likely to "
                              "not be a legitimate server")
        return False, ""  # Failed. Could be due to connection errors or wrong domain provided

    def _generate_headers_for_api_call(self):
        """Generates standardized headers to be fed into a HTTP request. A lack of these headers
        may cause the server's api to respond incorrectly"""
        headers = {
            "User-Agent": "YourApp/1.0",
            "Accept": "application/json",
        }
        return headers

    def _clean_user_provided_domain(self, user_provided_domain: str) -> str:
        """
        Private function to clean the user provided domain string, to get rid of variance
        in provided formats
        @param user_provided_domain: String provided by the user
        @return: Cleaned user domain (as a string)
        """
        parsed_input = urlparse(user_provided_domain)
        if parsed_input.scheme:
            # user provided http in string. This changes the way the standard library parses the url
            wanted_domain = parsed_input.netloc
        else:
            # user did not provide http in string
            wanted_domain = parsed_input.path
        return wanted_domain

    def start_app_api_client(self, user_domain: str,  client_id: str, client_secret: str, access_token: str):
        """
        Function to start the app client (client used by our app to authenticate users).
        This generated app client will be used to process user authorization requests

        Is not automatically called by init as we may not wish to start a client every time
        @param: user_domain: Mastodon.io, mstdn.io and the like; essentially, which server the user's
        account is located on
        @return: None, but there is a side effect of setting self.app_client
        """
        try:
            client = Mastodon(
                client_id=client_id,
                client_secret=client_secret,
                access_token=access_token,
                api_base_url=user_domain,
            )
            # Be careful: Wrong information used to start this client will not cause
            # the code to fail. Failure will only occur when the client is used later on
            self.app_client = client
        except (ConnectionError, MastodonAPIError) as err:
            self.logger.error("Encountered {e} when trying to start app_client".format(e=err))
            raise MastodonConnError("API client failed to start")

    def generate_redirect_url(self, num_tries=3) -> str:
        """
        Generates an url that the user will be redirected to in order to complete Mastodon's Oauth procedure
        @param: num_tries: Number of tries to generate a redirect url before giving up. Default value of 3
        @return: The redirect url as a string or None (upon connection failure)
        """
        assert self.app_client is not None, "App client has not been initialized"

        for i in range(num_tries):
            try:
                # It redirects the user to copy and paste an authorization code
                # Note that it does NOT check if the url generated is valid
                url = self.app_client.auth_request_url(redirect_uris=self.REDIRECT_URI, scopes=self.REQUIRED_SCOPES)
                return url
            except MastodonAPIError as err:
                self.logger.error(
                    "Encountered MastodonAPIError {e} in generate_redirect url. Retrying." "".format(e=err)
                )

        # This following code will only run if the above code failed n times.
        error_message = "Failed to generate url error after trying {n} times. Throwing error".format(n=num_tries)
        self.logger.error(error_message)
        raise MastodonConnError(error_message)

    def generate_user_access_token(self, user_auth_code: str, num_tries=3) -> str:
        """
        Uses the user's auth code to generate an access token that will serve as a way for our app to log
        in on the user's behalf
        @param user_auth_code: Provided by the user after going through the Mastodon OAuth Process
        @param num_tries: Number of times to repeat in case of failure before throwing exception
        @return: The user access token (as a str) that will allow our app to act on the user's behalf
        """
        assert self.app_client is not None, "App client has not been initialized"

        for i in range(num_tries):
            try:
                users_access_token = self.app_client.log_in(
                    code=user_auth_code,
                    redirect_uri=self.REDIRECT_URI,
                    scopes=self.REQUIRED_SCOPES,
                )
                return users_access_token
            except mastodon.errors.MastodonIllegalArgumentError as e:
                illegal_arg_error_msg = (
                    "Encountered error {e} trying to generate user access token. User "
                    "authorization code provided is likely invalid. Aborting".format(e=e)
                )
                self.logger.error(illegal_arg_error_msg)
                raise InvalidApiInputError(illegal_arg_error_msg)
            except (ConnectionError, MastodonAPIError) as err:
                self.logger.error("Encountered {e} when trying to generate_user_access_token." "Retrying".format(e=err))

        error_message = "Failed to generate user access token after trying {n} times. Throwing error".format(
            n=num_tries
        )
        self.logger.error(error_message)
        raise MastodonConnError(error_message)

    def check_if_domain_exists_in_database(self, domain_name):
        """
        Check if domain is already added in database with access token
        @param domain_name: Check if client_id, client_secret already exist for domain_name
        """
        domain = ApplicationTokens.query.filter_by(server=domain_name).first()
        if domain is None:
            return None
        else:
            return domain

    def add_domain_to_database(self, domain_name):
        """
        Add new domain to database. Fetch client id, client secret and access token and store it in database
        @param domain_name: Add domain_name to database, with its client id, client secret and access token
        """
        api_url = "https://" + domain_name + "/api/v1/apps"
        token_url = "https://" + domain_name + "/oauth/token"
        # TODO: Will need to refactor the code below into several functions
        payload = {
            'client_name': 'Test Application',
            'redirect_uris': 'urn:ietf:wg:oauth:2.0:oob',
            'scopes': 'read write push',
            'website': 'https://myapp.example'
        }
        try:
            headers = self._generate_headers_for_api_call()
            response = requests.post(api_url, data=payload, headers=headers)
            response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
            response_dict = json.loads(response.text)
            client_id = response_dict['client_id']
            client_secret = response_dict['client_secret']
            payload_token = {
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
                'grant_type': 'client_credentials'
            }
            response = requests.post(token_url, data=payload_token, headers=headers)
            response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
            response_dict_token = json.loads(response.text)
            access_token = response_dict_token['access_token']
            app_token = ApplicationTokens(server=domain_name, client_id=client_id, client_secret=client_secret,
                                          access_token=access_token)
            dbi.session.add(app_token)
            dbi.session.commit()
            return client_id, client_secret, access_token
        except requests.exceptions.RequestException as e:
            # Handle exceptions that might occur during the request
            print(f"Error: {e}")
            return None, None, None
