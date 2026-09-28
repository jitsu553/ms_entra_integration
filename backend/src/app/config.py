from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    tenant_id: str
    client_id: str
    client_secret: str
    mailbox_upn: str
    api_key: str

    graph_base_url: str = "https://graph.microsoft.com/v1.0"
    graph_scope: str = "https://graph.microsoft.com/.default"
    graph_authority_url: str = "https://login.microsoftonline.com"
    default_page_size: int = 25

    mail_folder_inbox: str = "inbox"
    mail_folder_drafts: str = "drafts"
    mail_folder_sentitems: str = "sentitems"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
