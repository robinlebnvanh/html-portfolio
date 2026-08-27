import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.admin_auth import create_access_token
from app.auth import require_admin_token


class AdminTokenTests(unittest.TestCase):
    def credentials(self, token: str, scheme: str = "Bearer"):
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=token)

    def test_missing_credentials_are_rejected(self):
        with self.assertRaisesRegex(HTTPException, "admin bearer token required") as error:
            require_admin_token(None)
        self.assertEqual(error.exception.status_code, 401)

    def test_invalid_credentials_are_rejected(self):
        with patch.dict("os.environ", {"ADMIN_API_TOKEN": "expected"}):
            with self.assertRaisesRegex(HTTPException, "invalid admin bearer token") as error:
                require_admin_token(self.credentials("wrong"))
        self.assertEqual(error.exception.status_code, 401)

    def test_valid_credentials_are_accepted(self):
        with patch.dict("os.environ", {"ADMIN_API_TOKEN": "expected"}):
            self.assertIsNone(require_admin_token(self.credentials("expected")))

    def test_signed_access_token_is_accepted(self):
        with patch.dict("os.environ", {"ADMIN_AUTH_SECRET": "secret"}, clear=True):
            token = create_access_token(
                {"id": 1, "email": "admin@example.com", "role": "admin"},
            )
            self.assertIsNone(require_admin_token(self.credentials(token)))

    def test_missing_server_configuration_fails_closed(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(
                HTTPException, "admin authentication is not configured"
            ) as error:
                require_admin_token(self.credentials("anything"))
        self.assertEqual(error.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
