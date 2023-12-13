import configparser

import unittest
from pathlib import Path


from feed_amalgamator import create_app
from http import HTTPStatus
from feed_amalgamator.constants.common_constants import USERNAME_FIELD, PASSWORD_FIELD
from feed_amalgamator.helpers.db_interface import User

from werkzeug.security import check_password_hash, generate_password_hash

from feed_amalgamator.helpers.db_interface import dbi
from feed_amalgamator.constants.error_messages import USER_ALREADY_EXISTS_MSG, INVALID_USERNAME_MSG, INVALID_PASSWORD_MSG


class TestAuthPage(unittest.TestCase):
    """Tests the endpoints in the auth page. These are closely to functional/integration tests than unit tests"""

    def setUp(self) -> None:
        test_config_loc = Path("configuration/test_mastodon_client_info.ini")
        parser = configparser.ConfigParser()
        parser.read(test_config_loc)
        test_db_name = parser["TEST_SETTINGS"]["test_db_location"]

        self.app = create_app(db_file_name=test_db_name)
        with self.app.app_context():
            dbi.drop_all()  # For a clean slate in the test db
            dbi.create_all()
        self.app.config.update(
            {
                "TESTING": True,
            }
        )

        self.page_root = "auth"

    def test_register_new_user(self):
        register_url = "{r}/register".format(r=self.page_root)
        client = self.app.test_client()
        response = client.get(register_url)

        self.assertEqual(HTTPStatus.OK, response.status_code)

        html_rendered = response.data.decode("utf-8")
        self.assertIn(r'Log In', html_rendered)

        # Test the Post
        test_user = "Gojo Satoru"
        test_password = "Infinite4oid!"

        response_with_post = client.post(register_url, data={USERNAME_FIELD: test_user,
                                                             PASSWORD_FIELD: test_password})

        decoded_post_response = response_with_post.data.decode("utf-8")

        with self.app.app_context():
            # Test that db insertion was correct
            items = User.query.filter_by(username=test_user).all()
            self.assertEqual(1, len(items))
            object_to_check = items[0]
            self.assertEqual(test_user, object_to_check.username)
            self.assertEqual(True, check_password_hash(object_to_check.password, test_password))

        # Check that we have been successfully redirected to the home page
        self.assertIn("/{r}/login".format(r=self.page_root), decoded_post_response)

    def test_register_existing_user(self):
        register_url = "{r}/register".format(r=self.page_root)
        client = self.app.test_client()
        client.get(register_url)

        # Register new user
        test_user = "Gojo Satoru"
        test_password = "Infinite4oid!"

        client.post(register_url, data={USERNAME_FIELD: test_user, PASSWORD_FIELD: test_password})

        # Try to register the same user again
        client.get(register_url)
        response = client.post(register_url, data={USERNAME_FIELD: test_user, PASSWORD_FIELD: test_password})
        decoded_response = response.data.decode("utf-8")
        self.assertIn(USER_ALREADY_EXISTS_MSG, decoded_response)

    def test_correct_log_in(self):
        login_url = "{r}/login".format(r=self.page_root)
        client = self.app.test_client()
        client.get(login_url)

        test_user = "Meowmaster"
        test_password = "Infinite4oid!"

        with self.app.app_context():
            # Insert the user inside the db first
            user = User(username=test_user, password=generate_password_hash(test_password))
            dbi.session.add(user)
            dbi.session.commit()

        # Check that log in is successful
        response = client.post(login_url, data={USERNAME_FIELD: test_user, PASSWORD_FIELD: test_password})
        decoded_response = response.data.decode("utf-8")
        self.assertIn("feed/home", decoded_response)  # Should be redirected to feed/home page

    def test_incorrect_log_in(self):
        login_url = "{r}/login".format(r=self.page_root)
        client = self.app.test_client()
        client.get(login_url)

        test_user = "Meowmaster"
        test_password = "Infinite4oid!"

        with self.app.app_context():
            # Insert the user inside the db first
            user = User(username=test_user, password=generate_password_hash(test_password))
            dbi.session.add(user)
            dbi.session.commit()

        response = client.post(login_url, data={USERNAME_FIELD: "undefined", PASSWORD_FIELD: test_password})
        decoded_response = response.data.decode("utf-8")
        self.assertIn(INVALID_USERNAME_MSG, decoded_response)

        pw_response = client.post(login_url, data={USERNAME_FIELD: test_user, PASSWORD_FIELD: "meow"})
        decoded_pw_response = pw_response.data.decode("utf-8")
        self.assertIn(INVALID_PASSWORD_MSG, decoded_pw_response)

    # TODO - Test password validation