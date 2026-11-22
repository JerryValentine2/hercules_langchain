import os
import sys
import types
import unittest
from unittest.mock import patch

os.environ.setdefault("MODEL_TIMEOUT_SECONDS", "60")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import run_message


class TestRunMessage(unittest.TestCase):
    def test_invalid_message(self):
        for value in (None, "", "  ", 42):
            with self.subTest(value=value):
                self.assertEqual(run_message(value)["status"], "error")

    def test_no_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            result = run_message("Hello")
        self.assertEqual(result["status"], "error")

    def test_success_uses_model(self):
        class FakeModel:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
            def invoke(self, message):
                self.message = message
                return types.SimpleNamespace(content="Hello from model")
        fake = types.ModuleType("langchain_google_genai")
        fake.ChatGoogleGenerativeAI = FakeModel
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test"}), patch.dict(sys.modules, {"langchain_google_genai": fake}):
            result = run_message("Hello")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["answer"], "Hello from model")

    def test_provider_failure_not_fabricated(self):
        class FailingModel:
            def __init__(self, **kwargs):
                pass
            def invoke(self, message):
                raise RuntimeError("provider down")
        fake = types.ModuleType("langchain_google_genai")
        fake.ChatGoogleGenerativeAI = FailingModel
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test"}), patch.dict(sys.modules, {"langchain_google_genai": fake}):
            result = run_message("Hello")
        self.assertEqual(result["status"], "error")
        self.assertNotIn("answer", result)


if __name__ == "__main__":
    unittest.main()
