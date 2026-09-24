from pydantic import BaseModel, EmailStr

from app.models.common import BodyType


class SendMailRequest(BaseModel):
    to: list[EmailStr]
    cc: list[EmailStr] = []
    bcc: list[EmailStr] = []
    subject: str
    body: str
    body_type: BodyType = BodyType.text
    save_to_sent_items: bool = True


class ReplyRequest(BaseModel):
    comment: str
    reply_all: bool = False


class ForwardRequest(BaseModel):
    comment: str
    to: list[EmailStr]
