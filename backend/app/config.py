from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://solair:solair_dev@localhost:5432/solair"
    database_url_sync: str = "postgresql://solair:solair_dev@localhost:5432/solair"
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic: str = "solair/#"

    class Config:
        env_file = ".env"


settings = Settings()
