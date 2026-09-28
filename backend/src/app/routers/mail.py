from typing import Any

from fastapi import APIRouter, Depends, Query

from app.deps import get_graph_client
from app.graph.client import GraphClient
from app.models.messages import ForwardRequest, ReplyRequest, SendMailRequest
from app.security import require_api_key

router = APIRouter(prefix="/mail", tags=["mail"], dependencies=[Depends(require_api_key)])

TopQuery = Query(default=25, ge=1, le=100, description="Max number of messages to return")
NextLinkQuery = Query(
    default=None,
    description="The @odata.nextLink from a previous page's response, to fetch the next page.",
)


@router.get(
    "/inbox",
    summary="List inbox messages",
    description="Lists messages in the mailbox's Inbox folder, newest first, "
    "as returned by Microsoft Graph. Pass the previous response's @odata.nextLink "
    "as next_link to fetch subsequent pages.",
)
async def list_inbox(
    top: int = TopQuery,
    next_link: str | None = NextLinkQuery,
    graph: GraphClient = Depends(get_graph_client),
) -> dict[str, Any]:
    return await graph.list_inbox_messages(top=top, next_link=next_link)


@router.get(
    "/drafts",
    summary="List draft messages",
    description="Lists messages in the mailbox's Drafts folder, as returned by Microsoft Graph. "
    "Pass the previous response's @odata.nextLink as next_link to fetch subsequent pages.",
)
async def list_drafts(
    top: int = TopQuery,
    next_link: str | None = NextLinkQuery,
    graph: GraphClient = Depends(get_graph_client),
) -> dict[str, Any]:
    return await graph.list_drafts(top=top, next_link=next_link)


@router.get(
    "/sentitems",
    summary="List sent messages",
    description="Lists messages in the mailbox's Sent Items folder, as returned by Microsoft "
    "Graph. Pass the previous response's @odata.nextLink as next_link to fetch subsequent pages.",
)
async def list_sent_items(
    top: int = TopQuery,
    next_link: str | None = NextLinkQuery,
    graph: GraphClient = Depends(get_graph_client),
) -> dict[str, Any]:
    return await graph.list_sent_items(top=top, next_link=next_link)


@router.get(
    "/folders/{folder}",
    summary="Get mail folder metadata",
    description="Fetches metadata for a mail folder (e.g. inbox, drafts, sentitems), including "
    "totalItemCount and unreadItemCount, as returned by Microsoft Graph.",
)
async def get_folder(
    folder: str,
    graph: GraphClient = Depends(get_graph_client),
) -> dict[str, Any]:
    return await graph.get_folder(folder)


@router.get(
    "/messages/{message_id}",
    summary="Get a single message",
    description="Fetches full details (including body) for one message by its Graph message ID, "
    "as returned by Microsoft Graph.",
)
async def get_message(
    message_id: str,
    graph: GraphClient = Depends(get_graph_client),
) -> dict[str, Any]:
    return await graph.get_message(message_id)


@router.get(
    "/messages/{message_id}/trail",
    summary="Get the mail trail for a message",
    description="Fetches every message in this mailbox sharing the same conversation "
    "(reply/forward trail) as the given message ID, oldest first, as returned by "
    "Microsoft Graph.",
)
async def get_message_trail(
    message_id: str,
    graph: GraphClient = Depends(get_graph_client),
) -> dict[str, Any]:
    return await graph.get_conversation(message_id)


@router.post(
    "/send",
    status_code=202,
    summary="Send a new email",
    description="Sends a new email from the mailbox. Returns 202 Accepted with no body, "
    "matching Graph's own sendMail behavior.",
)
async def send_mail(
    payload: SendMailRequest,
    graph: GraphClient = Depends(get_graph_client),
) -> None:
    await graph.send_mail(
        to=payload.to,
        cc=payload.cc,
        bcc=payload.bcc,
        subject=payload.subject,
        body=payload.body,
        body_type=payload.body_type.value,
        save_to_sent_items=payload.save_to_sent_items,
    )


@router.post(
    "/messages/{message_id}/reply",
    status_code=202,
    summary="Reply to a message",
    description="Replies (or reply-all) to an existing message by ID with a comment body.",
)
async def reply_to_message(
    message_id: str,
    payload: ReplyRequest,
    graph: GraphClient = Depends(get_graph_client),
) -> None:
    await graph.reply(message_id, comment=payload.comment, reply_all=payload.reply_all)


@router.post(
    "/messages/{message_id}/forward",
    status_code=202,
    summary="Forward a message",
    description="Forwards an existing message by ID to a new list of recipients with a comment.",
)
async def forward_message(
    message_id: str,
    payload: ForwardRequest,
    graph: GraphClient = Depends(get_graph_client),
) -> None:
    await graph.forward(message_id, comment=payload.comment, to=payload.to)
