import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.admin_auth import create_access_token
from app.auth import require_admin_token
from app.main import app


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

    def test_private_stock_read_routes_require_admin_token(self):
        private_paths = {
            "/api/v1/admin/summary",
            "/api/v1/stocks/portfolio",
            "/api/v1/stocks/journals",
        }

        for route in app.routes:
            if getattr(route, "path", None) in private_paths:
                dependency_calls = [
                    dependency.dependency for dependency in route.dependencies
                ]
                self.assertIn(require_admin_token, dependency_calls)
                private_paths.remove(route.path)

        self.assertEqual(private_paths, set())


if __name__ == "__main__":
    unittest.main()
