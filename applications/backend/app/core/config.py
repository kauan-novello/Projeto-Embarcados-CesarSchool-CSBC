from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str
    jwt_secret_key: str
    jwt_expire_minutes: int = 1440
    cookie_name: str = "solarsense_session"
    frontend_origin: str = "http://localhost:5173"

    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883
    mqtt_username: str
    mqtt_password: str

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_email_to: str = ""
    panel_overheat_threshold_c: float = 65.0

    mlflow_tracking_uri: str = "http://localhost:5000"
    registered_model_name: str = "solarsense-energy-hourly"


settings = Settings()  # type: ignore[call-arg]
