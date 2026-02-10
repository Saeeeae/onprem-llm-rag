"""Unit tests for shared.config module."""
import pytest
from shared.config import BaseServiceSettings, GPUServiceSettings


class TestBaseServiceSettings:
    def test_defaults(self):
        settings = BaseServiceSettings()
        assert settings.SERVICE_NAME == "unknown"
        assert settings.SERVICE_PORT == 8000
        assert settings.LOG_LEVEL == "INFO"
        assert settings.ENVIRONMENT == "production"
        assert settings.DEBUG is False
        assert settings.REDIS_HOST == "redis"
        assert settings.REDIS_PORT == 6379

    def test_custom_values(self, monkeypatch):
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_PORT", "9000")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        settings = BaseServiceSettings()
        assert settings.SERVICE_NAME == "test-service"
        assert settings.SERVICE_PORT == 9000
        assert settings.LOG_LEVEL == "DEBUG"


class TestGPUServiceSettings:
    def test_inherits_base(self):
        settings = GPUServiceSettings()
        assert settings.SERVICE_NAME == "unknown"
        assert settings.CUDA_VISIBLE_DEVICES == "0"
        assert settings.MODEL_PATH == ""
        assert settings.MODEL_NAME == ""

    def test_gpu_env_override(self, monkeypatch):
        monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0,1")
        monkeypatch.setenv("MODEL_PATH", "/models/test")
        settings = GPUServiceSettings()
        assert settings.CUDA_VISIBLE_DEVICES == "0,1"
        assert settings.MODEL_PATH == "/models/test"
