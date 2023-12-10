import configparser
import unittest
from pathlib import Path

from feed_amalgamator import create_app


class TestFeedPage(unittest.TestCase):
    """Tests the endpoints in the feed page. These are closely to functional/integration tests than unit tests"""

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