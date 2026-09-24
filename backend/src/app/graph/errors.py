import httpx


class GraphAPIError(Exception):
    def __init__(self, status_code: int, detail: str, retry_after: str | None = None):
        self.status_code = status_code
        self.detail = detail
        self.retry_after = retry_after
        super().__init__(detail)


class GraphAuthError(GraphAPIError):
    """Graph rejected our credentials (401) — this service's own config is broken."""


class GraphPermissionError(GraphAPIError):
    """Graph rejected the call due to insufficient permissions (403)."""


class GraphNotFoundError(GraphAPIError):
    """Requested resource does not exist in Graph (404)."""


class GraphThrottledError(GraphAPIError):
    """Graph is throttling requests (429)."""


def _extract_message(response: httpx.Response) -> str:
    try:
        body = response.json()
        return body.get("error", {}).get("message", response.text)
    except ValueError:
        return response.text


def raise_for_graph_status(response: httpx.Response) -> None:
    if response.status_code < 400:
        return

    message = _extract_message(response)

    if response.status_code == 401:
        raise GraphAuthError(401, message)
    if response.status_code == 403:
        raise GraphPermissionError(403, message)
    if response.status_code == 404:
        raise GraphNotFoundError(404, message)
    if response.status_code == 429:
        raise GraphThrottledError(429, message, retry_after=response.headers.get("Retry-After"))

    raise GraphAPIError(response.status_code, message)
