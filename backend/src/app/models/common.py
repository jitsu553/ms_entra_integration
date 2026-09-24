from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class BodyType(str, Enum):
    text = "Text"
    html = "HTML"


def _addresses(data: dict, field: str) -> list[str]:
    return [
        recipient.get("emailAddress", {}).get("address")
        for recipient in data.get(field, [])
        if recipient.get("emailAddress", {}).get("address")
    ]


class MessageSummary(BaseModel):
    id: str
    subject: str | None = None
    from_address: str | None = None
    received_date_time: datetime | None = None
    is_read: bool | None = None
    body_preview: str | None = None

    @classmethod
    def from_graph(cls, data: dict) -> "MessageSummary":
        email_address = (data.get("from") or {}).get("emailAddress") or {}
        return cls(
            id=data["id"],
            subject=data.get("subject"),
            from_address=email_address.get("address"),
            received_date_time=data.get("receivedDateTime"),
            is_read=data.get("isRead"),
            body_preview=data.get("bodyPreview"),
        )


class MessageDetail(MessageSummary):
    body_content_type: str | None = None
    body_content: str | None = None
    to_recipients: list[str] = []
    cc_recipients: list[str] = []

    @classmethod
    def from_graph(cls, data: dict) -> "MessageDetail":
        summary = MessageSummary.from_graph(data)
        body = data.get("body") or {}
        return cls(
            **summary.model_dump(),
            body_content_type=body.get("contentType"),
            body_content=body.get("content"),
            to_recipients=_addresses(data, "toRecipients"),
            cc_recipients=_addresses(data, "ccRecipients"),
        )


class MessageListResponse(BaseModel):
    value: list[MessageSummary]
    next_link: str | None = None

    @classmethod
    def from_graph(cls, data: dict) -> "MessageListResponse":
        return cls(
            value=[MessageSummary.from_graph(item) for item in data.get("value", [])],
            next_link=data.get("@odata.nextLink"),
        )
