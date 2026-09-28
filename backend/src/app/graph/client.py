from typing import Any

import httpx
import msal

from app.config import Settings
from app.graph.errors import GraphAuthError, raise_for_graph_status


def _recipients(addresses: list[str]) -> list[dict[str, Any]]:
    return [{"emailAddress": {"address": address}} for address in addresses]


class GraphClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._msal_app = msal.ConfidentialClientApplication(
            client_id=settings.client_id,
            client_credential=settings.client_secret,
            authority=f"{settings.graph_authority_url}/{settings.tenant_id}",
        )
        self._http = httpx.AsyncClient(base_url=settings.graph_base_url, timeout=30.0)
        self._mailbox_path = f"/users/{settings.mailbox_upn}"

    async def aclose(self) -> None:
        await self._http.aclose()

    def _get_token(self) -> str:
        result = self._msal_app.acquire_token_for_client(scopes=[self._settings.graph_scope])
        if "access_token" not in result:
            raise GraphAuthError(
                401, result.get("error_description", "Failed to acquire Graph access token")
            )
        return result["access_token"]

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        token = self._get_token()
        headers = {
            "Prefer": 'outlook.body-content-type="text"',
            **kwargs.pop("headers", {}),
        }
        headers["Authorization"] = f"Bearer {token}"
        response = await self._http.request(method, path, headers=headers, **kwargs)
        raise_for_graph_status(response)
        return response

    async def _list_messages(
        self, folder: str, top: int, next_link: str | None = None
    ) -> dict:
        if next_link:
            response = await self._request("GET", next_link)
        else:
            response = await self._request(
                "GET",
                f"{self._mailbox_path}/mailFolders/{folder}/messages",
                params={"$top": top},
            )
        return response.json()

    async def list_inbox_messages(self, top: int, next_link: str | None = None) -> dict:
        return await self._list_messages(self._settings.mail_folder_inbox, top, next_link)

    async def list_drafts(self, top: int, next_link: str | None = None) -> dict:
        return await self._list_messages(self._settings.mail_folder_drafts, top, next_link)

    async def list_sent_items(self, top: int, next_link: str | None = None) -> dict:
        return await self._list_messages(self._settings.mail_folder_sentitems, top, next_link)

    async def get_folder(self, folder: str) -> dict:
        response = await self._request("GET", f"{self._mailbox_path}/mailFolders/{folder}")
        return response.json()

    async def get_message(self, message_id: str) -> dict:
        response = await self._request("GET", f"{self._mailbox_path}/messages/{message_id}")
        return response.json()

    async def get_conversation(self, message_id: str) -> dict:
        message = await self.get_message(message_id)
        conversation_id = message["conversationId"]
        response = await self._request(
            "GET",
            f"{self._mailbox_path}/messages",
            params={
                "$filter": f"conversationId eq '{conversation_id}'",
                "$count": "true",
            },
            headers={"ConsistencyLevel": "eventual"},
        )
        data = response.json()
        data["value"].sort(key=lambda item: item["receivedDateTime"])
        return data

    async def send_mail(
        self,
        to: list[str],
        cc: list[str],
        bcc: list[str],
        subject: str,
        body: str,
        body_type: str,
        save_to_sent_items: bool,
    ) -> None:
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": body_type, "content": body},
                "toRecipients": _recipients(to),
                "ccRecipients": _recipients(cc),
                "bccRecipients": _recipients(bcc),
            },
            "saveToSentItems": save_to_sent_items,
        }
        await self._request("POST", f"{self._mailbox_path}/sendMail", json=payload)

    async def reply(self, message_id: str, comment: str, reply_all: bool) -> None:
        action = "replyAll" if reply_all else "reply"
        await self._request(
            "POST",
            f"{self._mailbox_path}/messages/{message_id}/{action}",
            json={"comment": comment},
        )

    async def forward(self, message_id: str, comment: str, to: list[str]) -> None:
        payload = {"comment": comment, "toRecipients": _recipients(to)}
        await self._request(
            "POST",
            f"{self._mailbox_path}/messages/{message_id}/forward",
            json=payload,
        )
