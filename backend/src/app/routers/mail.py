from fastapi import APIRouter, Depends, Query

from app.deps import get_graph_client
from app.graph.client import GraphClient
from app.models.common import MessageDetail, MessageListResponse
from app.models.messages import ForwardRequest, ReplyRequest, SendMailRequest
from app.security import require_api_key

router = APIRouter(prefix="/mail", tags=["mail"], dependencies=[Depends(require_api_key)])

TopQuery = Query(default=25, ge=1, le=100, description="Max number of messages to return")


@router.get(
    "/inbox",
    response_model=MessageListResponse,
    summary="List inbox messages",
    description="Lists messages in the mailbox's Inbox folder, newest first.",
)
async def list_inbox(
    top: int = TopQuery,
    graph: GraphClient = Depends(get_graph_client),
) -> MessageListResponse:
    data = await graph.list_inbox_messages(top=top)
    return MessageListResponse.from_graph(data)


@router.get(
    "/drafts",
    response_model=MessageListResponse,
    summary="List draft messages",
    description="Lists messages in the mailbox's Drafts folder.",
)
async def list_drafts(
    top: int = TopQuery,
    graph: GraphClient = Depends(get_graph_client),
) -> MessageListResponse:
    data = await graph.list_drafts(top=top)
    return MessageListResponse.from_graph(data)


@router.get(
    "/sentitems",
    response_model=MessageListResponse,
    summary="List sent messages",
    description="Lists messages in the mailbox's Sent Items folder.",
)
async def list_sent_items(
    top: int = TopQuery,
    graph: GraphClient = Depends(get_graph_client),
) -> MessageListResponse:
    data = await graph.list_sent_items(top=top)
    return MessageListResponse.from_graph(data)


@router.get(
    "/messages/{message_id}",
    response_model=MessageDetail,
    summary="Get a single message",
    description="Fetches full details (including body) for one message by its Graph message ID.",
)
async def get_message(
    message_id: str,
    graph: GraphClient = Depends(get_graph_client),
) -> MessageDetail:
    data = await graph.get_message(message_id)
    return MessageDetail.from_graph(data)


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
