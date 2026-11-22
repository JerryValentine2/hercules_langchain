import os
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import run_message, build_model


class TestRunMessage(unittest.TestCase):
    def test_invalid_message(self):
        for value in (None, "", "  ", 42):
            with self.subTest(value=value):
                self.assertEqual(run_message(value)["status"], "error")

    def test_invalid_path(self):
        self.assertEqual(run_message("Hello", path="unknown")["status"], "error")

    def test_default_gemini_without_api_key(self):
        class FakeModel:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
            def invoke(self, message):
                return types.SimpleNamespace(content="Hello from Gemini")
        fake = types.ModuleType("langchain_google_vertexai")
        fake.ChatVertexAI = FakeModel
        with patch.dict(os.environ, {}, clear=True), patch.dict(sys.modules, {"langchain_google_vertexai": fake}):
            result = run_message("Hello")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["answer"], "Hello from Gemini")

    def test_explicit_gemini(self):
        class FakeModel:
            def __init__(self, **kwargs):
                pass
            def invoke(self, message):
                return types.SimpleNamespace(content="Gemini")
        fake = types.ModuleType("langchain_google_vertexai")
        fake.ChatVertexAI = FakeModel
        with patch.dict(sys.modules, {"langchain_google_vertexai": fake}):
            self.assertEqual(run_message("Hi", path="gemini")["status"], "success")

    def test_external_missing_config(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(run_message("Hello", path="external")["status"], "error")

    def test_external_adapter_constructed(self):
        class FakeModel:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
        fake = types.ModuleType("langchain_openai")
        fake.ChatOpenAI = FakeModel
        env = {"EXTERNAL_MODEL": "example-model", "EXTERNAL_BASE_URL": "https://example.invalid/v1", "EXTERNAL_API_KEY": "test"}
        with patch.dict(os.environ, env), patch.dict(sys.modules, {"langchain_openai": fake}):
            model, name = build_model("external")
        self.assertEqual(name, "example-model")
        self.assertEqual(model.kwargs["base_url"], env["EXTERNAL_BASE_URL"])

    def test_model_failure_not_fabricated(self):
        class FailingModel:
            def __init__(self, **kwargs):
                pass
            def invoke(self, message):
                raise RuntimeError("provider down")
        fake = types.ModuleType("langchain_google_vertexai")
        fake.ChatVertexAI = FailingModel
        with patch.dict(sys.modules, {"langchain_google_vertexai": fake}):
            result = run_message("Hello")
        self.assertEqual(result["status"], "error")
        self.assertNotIn("answer", result)


if __name__ == "__main__":
    unittest.main()
