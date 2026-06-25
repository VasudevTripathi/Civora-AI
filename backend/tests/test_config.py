from backend.app.core.config import Settings


def test_cors_origins_parsing():
    # Test that CORS origins string gets parsed into a list
    settings = Settings(BACKEND_CORS_ORIGINS="http://localhost:3000,http://localhost:5000")
    assert settings.BACKEND_CORS_ORIGINS == ["http://localhost:3000", "http://localhost:5000"]

    # Test that list remains list
    settings_list = Settings(BACKEND_CORS_ORIGINS=["http://localhost:3000"])
    assert settings_list.BACKEND_CORS_ORIGINS == ["http://localhost:3000"]


def test_default_paths():
    settings = Settings()
    assert settings.PROJECT_NAME == "Civora AI"
    assert "data" in settings.DATA_DIR
    assert "knowledge" in settings.KNOWLEDGE_DIR
