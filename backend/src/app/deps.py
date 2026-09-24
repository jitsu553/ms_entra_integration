from fastapi import Request

from app.graph.client import GraphClient


def get_graph_client(request: Request) -> GraphClient:
    return request.app.state.graph_client
