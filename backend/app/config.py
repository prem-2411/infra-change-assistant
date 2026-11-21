"""Settings read from environment variables (never hard-code secrets)."""
import os


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
        self.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")
        self.token_minutes = _int("TOKEN_MINUTES", 30)

        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.llm_model = os.getenv("LLM_MODEL", "claude-sonnet-5-5")
        self.llm_timeout_seconds = float(os.getenv("LLM_TIMEOUT_SECONDS", "45"))
        self.llm_max_turns = _int("LLM_MAX_TURNS", 6)

        self.login_rate_limit = _int("LOGIN_RATE_LIMIT", 10)
        self.login_rate_window = _int("LOGIN_RATE_WINDOW", 60)
        self.review_rate_limit = _int("REVIEW_RATE_LIMIT", 10)
        self.review_rate_window = _int("REVIEW_RATE_WINDOW", 60)
        # Only trust X-Forwarded-For when running behind your own reverse proxy.
        self.trust_proxy = os.getenv("TRUST_PROXY", "false").lower() == "true"

        self.admin_email = os.getenv("ADMIN_EMAIL", "").lower()
        self.admin_password = os.getenv("ADMIN_PASSWORD", "")
        self.seed_demo_users = os.getenv("SEED_DEMO_USERS", "false").lower() == "true"
        self.demo_password = os.getenv("DEMO_PASSWORD", "")
        self.cors_origins = [o for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o]


settings = Settings()
