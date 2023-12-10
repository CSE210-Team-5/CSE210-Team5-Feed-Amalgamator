import configparser

import unittest
from pathlib import Path


from feed_amalgamator import create_app
from http import HTTPStatus
from feed_amalgamator.CONFIG import USERNAME_FIELD, PASSWORD_FIELD
from feed_amalgamator.helpers.db_interface import User

from werkzeug.security import check_password_hash


class TestAuthPage(unittest.TestCase):
    """Tests the endpoints in the auth page. These are closely to functional/integration tests than unit tests"""

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

        self.page_root = "auth"

    def test_register_page(self):
        register_url = "{r}/register".format(r=self.page_root)
        client = self.app.test_client()
        response = client.get(register_url)

        self.assertEqual(HTTPStatus.OK, response.status_code)

        # These may need to be updated if the html changes
        html_rendered = response.data.decode("utf-8")
        self.assertIn(r'input name="username"', html_rendered)
        self.assertIn(r'input type="password"', html_rendered)

        # Test the Post
        test_user = "Gojo Satoru"
        test_password = "Infinite Void!"
        client.post(register_url, data={USERNAME_FIELD: test_user, PASSWORD_FIELD: test_password})
        # decoded_post_response = response_with_post.data.decode("utf-8")
        with self.app.app_context():
            # Test that db insertion was correct
            items = User.query.filter_by(username=test_user).all()
            self.assertEqual(1, len(items))
            object_to_check = items[0]
            self.assertEqual(test_user, object_to_check.username)
            self.assertEqual(True, check_password_hash(object_to_check.password, test_password))

        # Test that redirect after login works correctly
        # May need to be changed if the design of the page
        # TODO - Figure out how testing works with redirects
        # print(decoded_post_response)
        # self.assertIn('value="Log In"', decoded_post_response)
