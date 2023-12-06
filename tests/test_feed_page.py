import configparser
import unittest
from pathlib import Path

from feed_amalgamator import create_app
from feed_amalgamator.feed import USER_DOMAIN_FIELD
from feed_amalgamator.helpers.db_interface import ApplicationTokens


class TestFeedPage(unittest.TestCase):
    """Tests the endpoints in the feed page. These are closely to functional/integration tests than unit tests"""
    def setUp(self) -> None:
        test_config_loc = Path("configuration/test_mastodon_client_info.ini")
        parser = configparser.ConfigParser()
        parser.read(test_config_loc)
        # test_log_root = parser["TEST_SETTINGS"]["test_log_root"]
        test_db_name = parser["TEST_SETTINGS"]["test_db_location"]

        self.app = create_app(db_file_name=test_db_name)
        self.app.config.update({
            "TESTING": True,
        })

        self.page_root = "feed"

    """
    This will require several dummy accounts to test the amalgamation
    
    def test_feed_home(self):
    client = self.app.test_client()
    home_url = "{r}/home".format(r=self.page_root)
    with client:
        # No users existing so far
        self.assertRaises(Exception, client.get(home_url))
    """

    def test_add_server_redirect_url(self):
        client = self.app.test_client()
        add_server_url = "{r}/add_server".format(r=self.page_root)
        # Testing garbage domain field
        self.assertRaises(Exception, client.post, add_server_url, data={USER_DOMAIN_FIELD: "garbage"})

        # Testing proper field
        proper_domain = "mastodon.social"
        with self.app.app_context():
            proper_post = client.post(add_server_url, data={USER_DOMAIN_FIELD: proper_domain})
            decoded_post_response = proper_post.data.decode("utf-8")
            items = ApplicationTokens.query.filter_by(server=proper_domain).all()
            self.assertEqual(1, len(items))  # Database insert successful
            # Authorization Token is a term that should appear in the page
            self.assertIn("Authorization Token", decoded_post_response)
            # Test by proxy that the generated url is in the page, but the actual redirect url generation function
            # should be tested elsewhere
            self.assertIn(proper_domain, decoded_post_response)

        # The auth token path cannot be tested as it requires an authorization code, which requires manual
        # intervention
