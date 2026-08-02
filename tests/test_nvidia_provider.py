import os
import unittest
from unittest.mock import patch

from backend.model_registry import model_for_agent
from backend.providers.nvidia import NvidiaConfig, NvidiaProviderError


class NvidiaConfigTests(unittest.TestCase):
    def test_missing_key_fails_closed(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            self.assertRaises(NvidiaProviderError),
        ):
            NvidiaConfig.from_env()

    def test_agent_override(self):
        with patch.dict(
            os.environ,
            {"NVIDIA_MODEL_FRONTEND": "meta/llama-3.2-3b-instruct"},
            clear=True,
        ):
            self.assertEqual(
                model_for_agent("frontend").model,
                "meta/llama-3.2-3b-instruct",
            )

    def test_default(self):
        with patch.dict(
            os.environ,
            {"NVIDIA_DEFAULT_MODEL": "openai/gpt-oss-20b"},
            clear=True,
        ):
            self.assertEqual(
                model_for_agent("planner").model,
                "openai/gpt-oss-20b",
            )


if __name__ == "__main__":
    unittest.main()
