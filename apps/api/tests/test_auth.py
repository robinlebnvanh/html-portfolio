import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.admin_auth import create_access_token
from app.auth import require_admin_token
from app.main import app, signed_cloudinary_upload_params


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
            "/api/v1/admin/uploads/cloudinary-signature",
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

    def test_cloudinary_signature_requires_server_configuration(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(HTTPException, "Cloudinary upload is not configured") as error:
                signed_cloudinary_upload_params()
        self.assertEqual(error.exception.status_code, 503)

    def test_cloudinary_signature_hides_api_secret(self):
        with patch.dict(
            "os.environ",
            {
                "CLOUDINARY_CLOUD_NAME": "demo-cloud",
                "CLOUDINARY_API_KEY": "demo-key",
                "CLOUDINARY_API_SECRET": "demo-secret",
                "CLOUDINARY_UPLOAD_FOLDER": "prj008/blog",
            },
            clear=True,
        ):
            upload = signed_cloudinary_upload_params()

        self.assertEqual(upload["cloud_name"], "demo-cloud")
        self.assertEqual(upload["api_key"], "demo-key")
        self.assertEqual(upload["asset_folder"], "prj008/blog")
        self.assertIn("signature", upload)
        self.assertNotIn("api_secret", upload)


if __name__ == "__main__":
    unittest.main()
