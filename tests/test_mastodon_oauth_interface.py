import unittest
import logging
import configparser
from pathlib import Path

from feed_amalgamator.helpers.custom_exceptions import InvalidApiInputError
from feed_amalgamator.helpers.logging_helper import LoggingHelper
from feed_amalgamator.helpers.mastodon_oauth_interface import MastodonOAuthInterface


class TestOauthInterface(unittest.TestCase):
    def setUp(self) -> None:
        test_config_loc = Path("configuration/test_mastodon_client_info.ini")
        parser = configparser.ConfigParser()
        parser.read(test_config_loc)
        test_log_root = parser["TEST_SETTINGS"]["test_log_root"]

        logger_name = "oauth_interface_test"
        test_log_file = Path("{r}/{n}.log".format(r=test_log_root, n=logger_name))
        logger = LoggingHelper.generate_logger(logging.INFO, test_log_file, logger_name)
        self.logger = logger
        self.client = MastodonOAuthInterface(logger)

        tokens_dict = parser["APP_TOKENS"]
        self.client_domain = tokens_dict["CLIENT_DOMAIN"]  # Required to be passed in as a parameter
        self.client_id = tokens_dict["CLIENT_ID"]
        self.client_secret = tokens_dict["CLIENT_SECRET"]
        self.access_token = tokens_dict["ACCESS_TOKEN"]

    def test_verify_user_provided_domain(self):
        with_https = "https://mastodon.social"
        without_https = "www.mastodon.social"

        wanted_result = "mastodon.social"
        self.assertEqual((True, wanted_result), self.client.verify_user_provided_domain(with_https))
        self.assertEqual((True, wanted_result), self.client.verify_user_provided_domain(without_https))

        mangled_domain = "mastodo.social"
        self.assertEqual(self.client.verify_user_provided_domain(mangled_domain)[0], False)

    def test_generate_user_token(self):
        # No client has been started yet, AssertionError should be thrown
        self.assertRaises(AssertionError, self.client.generate_user_access_token, "undefined")

        self.client.start_app_api_client(self.client_domain, self.client_id,
                                         self.client_secret, self.access_token)  # Sets self.api_client

        wrong_auth_code = "Sousou no Frieren"

        self.assertRaises(InvalidApiInputError, self.client.generate_user_access_token,
                          wrong_auth_code)

        # Testing a CORRECT auth code cannot be done automatically as it requires
        # a manual redirect to a page where a user has to log in. As such, we only test the wrong situation
