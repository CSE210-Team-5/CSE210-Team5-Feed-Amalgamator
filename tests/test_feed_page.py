import configparser
import unittest
from pathlib import Path

from werkzeug.security import generate_password_hash

from feed_amalgamator import create_app, dbi
from feed_amalgamator.constants.common_constants import USER_ID_FIELD, USER_DOMAIN_FIELD, SERVERS_FIELD
from feed_amalgamator.constants.error_messages import NO_CONTENT_FOUND_MSG, INVALID_MASTODON_DOMAIN_MSG, \
    INVALID_DELETE_SERVER_RECORD_MSG
from feed_amalgamator.helpers.db_interface import User, ApplicationTokens, UserServer


class TestFeedPage(unittest.TestCase):
    """Tests the endpoints in the feed page. These are closely to functional/integration tests than unit tests,
    and do depend on tokens such as app tokens that were previous generated for exclusive test use"""
    def setUp(self) -> None:
        test_config_loc = Path("configuration/test_mastodon_client_info.ini")
        parser = configparser.ConfigParser()
        parser.read(test_config_loc)
        # test_log_root = parser["TEST_SETTINGS"]["test_log_root"]
        test_db_name = parser["TEST_SETTINGS"]["test_db_location"]

        self.app = create_app(db_file_name=test_db_name)
        self.app.config.update(
            {
                "TESTING": True,
            }
        )

        with self.app.app_context():
            dbi.drop_all()  # For a clean slate in the test db
            dbi.create_all()

        self.page_root = "feed"
        self.redirect_uri = parser["REDIRECT_URI"]["redirect_uri"]
        test_client_settings = parser["APP_TOKENS"]
        self.client_id = test_client_settings["CLIENT_ID"]
        self.client_secret = test_client_settings["CLIENT_SECRET"]
        self.access_token = test_client_settings["ACCESS_TOKEN"]  # Bot's access token
        self.client_domain = test_client_settings["CLIENT_DOMAIN"]
        self.user_token_server_one = test_client_settings["USER_TOKEN_SERVER_ONE"]  # User token generated after oauth

        # Credentials for second client for another server
        self.alt_client_id = test_client_settings["ALT_CLIENT_ID"]
        self.alt_client_secret = test_client_settings["ALT_CLIENT_SECRET"]
        self.alt_access_token = test_client_settings["ALT_ACCESS_TOKEN"]
        self.alt_client_domain = test_client_settings["ALT_CLIENT_DOMAIN"]
        self.user_token_server_two = test_client_settings["USER_TOKEN_SERVER_TWO"]

    def test_feed_amalgamation(self):
        client = self.app.test_client()
        home_url = "{r}/home".format(r=self.page_root)
        test_user = "Meowmaster"
        test_password = "Infinite4oid!"

        with self.app.app_context():
            user = User(username=test_user, password=generate_password_hash(test_password))
            dbi.session.add(user)
            dbi.session.commit()

            user_server_one = UserServer(user_id=1, server=self.client_domain, token=self.user_token_server_one)
            user_server_two = UserServer(user_id=1, server=self.alt_client_domain, token=self.user_token_server_two)
            dbi.session.add(user_server_one)
            dbi.session.add(user_server_two)
            dbi.session.commit()

        with client.session_transaction() as sess:
            sess[USER_ID_FIELD] = 1

        response = client.get(home_url)
        decoded_resp = response.data.decode("utf-8")

        self.assertIn(self.client_domain, decoded_resp)
        self.assertIn(self.alt_client_domain, decoded_resp)

    def test_no_servers_added(self):
        """Proper error message should be found when the user has no servers added but visits the home page"""
        client = self.app.test_client()
        home_url = "{r}/home".format(r=self.page_root)

        # With no user in the session, should be redirected to login page
        response = client.get(home_url)
        decoded_resp = response.data.decode("utf-8")
        self.assertIn("auth/login", decoded_resp)

        test_user = "Meowmaster"
        test_password = "Infinite4oid!"
        with self.app.app_context():
            user = User(username=test_user, password=generate_password_hash(test_password))
            dbi.session.add(user)
            dbi.session.commit()

        with client.session_transaction() as sess:
            sess[USER_ID_FIELD] = 1  # Using id, not the username

        response = client.get(home_url)
        decoded_resp = response.data.decode("utf-8")
        self.assertIn(NO_CONTENT_FOUND_MSG, decoded_resp)

    def test_add_server_redirect_url_for_garbage_domain(self):
        client = self.app.test_client()
        add_server_url = "{r}/add_server".format(r=self.page_root)
        # Testing garbage domain field
        garbage_domain = "wemionweiofwubb.io"
        response = client.post(add_server_url, data={USER_DOMAIN_FIELD: garbage_domain})
        decoded_response = response.data.decode("utf-8")
        self.assertIn(INVALID_MASTODON_DOMAIN_MSG, decoded_response)
        self.assertIn(garbage_domain, decoded_response)

    def test_add_server_redirect_url_for_proper_domain(self):
        """There are two potential cases here: One where we already have a client for a given domain
        in the database, and one where we do not have such a client available.
        We are only unit testing the former, as the second would involve creating yet another client with mastodon.
        Doing so repeatedly may lead to complaints from mastodon"""
        client = self.app.test_client()
        with self.app.app_context():
            # Adding test client to test db
            app_token = ApplicationTokens(server=self.client_domain, client_id=self.client_id,
                                          client_secret=self.client_secret,
                                          access_token=self.access_token, redirect_uri=self.redirect_uri)
            dbi.session.add(app_token)
            dbi.session.commit()

        add_server_url = "{r}/add_server".format(r=self.page_root)
        response = client.post(add_server_url, data={USER_DOMAIN_FIELD: self.client_domain})
        decoded_response = response.data.decode("utf-8")

        self.assertIn("oauth/authorize", decoded_response)  # Ensure that users are redirected to the correct page
        self.assertIn(self.client_domain, decoded_response)

    def test_delete_server(self):
        test_user = "Meowmaster"
        test_password = "Infinite4oid!"
        with self.app.app_context():
            # Setting up necessary entries in the test db
            user = User(username=test_user, password=generate_password_hash(test_password))
            dbi.session.add(user)
            dbi.session.commit()
            # Now we can add the servers
            server_one = UserServer(user_id=1, server="serverOne", token="tokenOne")
            server_two = UserServer(user_id=1, server="serverTwo", token="tokenTwo")
            server_three = UserServer(user_id=1, server="serverThree", token="tokenThree")
            dbi.session.add(server_one)
            dbi.session.add(server_two)
            dbi.session.add(server_three)
            dbi.session.commit()

            # Actual test
            client = self.app.test_client()
            with client.session_transaction() as sess:
                sess[USER_ID_FIELD] = 1  # Using id, not the username

            delete_server_url = "{r}/delete_server".format(r=self.page_root)
            client.post(delete_server_url, data={SERVERS_FIELD: ["serverTwo", "serverThree"]})

            servers_after_delete = UserServer.query.filter_by(user_id=1).all()
            self.assertEqual(1, len(servers_after_delete))

            # Test deleting server that does not exist
            error_resp = client.post(delete_server_url, data={SERVERS_FIELD: ["MEOW"]})
            self.assertIn(INVALID_DELETE_SERVER_RECORD_MSG, error_resp.data.decode("utf-8"))
