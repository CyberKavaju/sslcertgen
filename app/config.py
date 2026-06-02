import os


class BaseConfig:
    APP_NAME = "tls-cert-generator"
    TESTING = False

    @staticmethod
    def secret_key() -> str:
        return os.getenv("SECRET_KEY", "dev-insecure-change-me")

    @staticmethod
    def _env_bool(name: str, default: bool) -> bool:
        raw_value = os.getenv(name)
        if raw_value is None:
            return default
        return raw_value.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def rate_limit_per_ip() -> str:
        return os.getenv("RATE_LIMIT_PER_IP", "10/minute")

    @staticmethod
    def limiter_storage_uri() -> str:
        return os.getenv("RATELIMIT_STORAGE_URI", "memory://")

    @staticmethod
    def max_content_length() -> int:
        return int(os.getenv("MAX_CONTENT_LENGTH", "8192"))

    @staticmethod
    def max_domain_length() -> int:
        return int(os.getenv("MAX_DOMAIN_LENGTH", "253"))

    @staticmethod
    def trust_proxy_hops() -> int:
        return int(os.getenv("TRUST_PROXY_HOPS", "1"))

    @staticmethod
    def https_enforcement_enabled() -> bool:
        return BaseConfig._env_bool("HTTPS_ENFORCEMENT_ENABLED", False)

    @staticmethod
    def security_headers_enabled() -> bool:
        return BaseConfig._env_bool("SECURITY_HEADERS_ENABLED", True)

    @staticmethod
    def hsts_enabled() -> bool:
        return BaseConfig._env_bool("HSTS_ENABLED", False)

    @staticmethod
    def hsts_max_age() -> int:
        return int(os.getenv("HSTS_MAX_AGE", "31536000"))

    @staticmethod
    def hsts_include_subdomains() -> bool:
        return BaseConfig._env_bool("HSTS_INCLUDE_SUBDOMAINS", True)

    @staticmethod
    def hsts_preload() -> bool:
        return BaseConfig._env_bool("HSTS_PRELOAD", False)

    @staticmethod
    def content_security_policy() -> str:
        return os.getenv(
            "CONTENT_SECURITY_POLICY",
            "default-src 'self'; script-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
        )

    @staticmethod
    def wizard_session_ttl_seconds() -> int:
        return int(os.getenv("WIZARD_SESSION_TTL_SECONDS", "1800"))

    @staticmethod
    def wizard_session_secret() -> str:
        return os.getenv("WIZARD_SESSION_SECRET", BaseConfig.secret_key())

    @staticmethod
    def wizard_start_rate_limit() -> str:
        return os.getenv("WIZARD_START_RATE_LIMIT", "10/minute")

    @staticmethod
    def wizard_verify_rate_limit() -> str:
        return os.getenv("WIZARD_VERIFY_RATE_LIMIT", "30/minute")

    @staticmethod
    def wizard_generate_rate_limit() -> str:
        return os.getenv("WIZARD_GENERATE_RATE_LIMIT", "5/minute")


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True


class ProductionConfig(BaseConfig):
    DEBUG = False


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
