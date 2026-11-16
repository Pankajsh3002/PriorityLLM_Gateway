import json
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    redis_url: str = "redis://localhost:6379/0"
    provider_mode: str = "mock" # "mock" or "openrouter"
    openrouter_api_key: str = ""
    scheduling: str = "priority" # "priority" or "fifo" (for A/B benchmarks)
    worker_concurrency: int = 8 # simulated upstream capacity
    request_timeout_s: float = 60.0
    # JSON: {"api-key": {"name": ..., "rpm": ..., "burst": ..., "monthly_tokens": ...}}
    tenants_json: str = (
    '{"demo-key": {"name": "demo", "rpm": 600, "burst": 50,'
    ' "monthly_tokens": 5000000}}'
    )
    # model alias -> ordered list of real models (first = preferred)
    routes_json: str = (
    '{"fast": ["mock-a", "mock-b"], "default": ["mock-a", "mock-b", "mock-c"]}'
    )
    # USD per 1M tokens: [input, output]. Used for cost + savings metrics.
    prices_json: str = (
    '{"mock-a": [0.5, 1.5], "mock-b": [0.2, 0.6], "mock-c": [0.1, 0.3]}'
    )
    @property
    def prices(self) -> dict:
        return json.loads(self.prices_json)
    @property
    def tenants(self) -> dict:
        return json.loads(self.tenants_json)
    @property
    def routes(self) -> dict:
        return json.loads(self.routes_json)

        
settings = Settings()
