"""封装 Elasticsearch 文档索引的常用操作，方便统一维护。"""
from typing import List, Optional

from elasticsearch import NotFoundError
from flask import current_app

from ..extensions import es

DOCUMENT_INDEX = "documents"
DEFAULT_SEARCH_SIZE = 100


def _get_client():
    return es


def _serialize_datetime(value):
    return value.isoformat() if value else None


def index_document(doc) -> bool:
    """将文档写入或更新到 Elasticsearch 索引中。"""
    client = _get_client()
    if not client or doc is None:
        return False

    try:
        client.index(
            index=DOCUMENT_INDEX,
            id=doc.id,
            document={
                "title": doc.title,
                "content": doc.content or "",
                "owner_id": doc.owner_id,
                "created_at": _serialize_datetime(doc.created_at),
                "updated_at": _serialize_datetime(doc.updated_at),
            },
            refresh="wait_for",
        )
        return True
    except Exception as exc:  # pylint: disable=broad-except
        current_app.logger.warning("Failed to index document %s: %s", doc.id, exc)
        return False


def delete_document_from_index(doc_id: int) -> bool:
    """根据文档 ID 从 Elasticsearch 中删除记录。"""
    client = _get_client()
    if not client or not doc_id:
        return False

    try:
        client.delete(index=DOCUMENT_INDEX, id=doc_id, ignore=[404], refresh="wait_for")
        return True
    except NotFoundError:
        return True
    except Exception as exc:  # pylint: disable=broad-except
        current_app.logger.warning("Failed to delete document %s from index: %s", doc_id, exc)
        return False


def search_document_ids(query: str, owner_id: int, limit: int = DEFAULT_SEARCH_SIZE) -> Optional[List[int]]:
    """基于关键词与用户 ID 在 Elasticsearch 中搜索，返回匹配的文档 ID 顺序。

    若 ES 客户端不可用或查询异常，返回 None 以便调用方回退数据库模糊匹配；
    若 ES 可用但无匹配结果，则返回空列表。
    """
    client = _get_client()
    keyword = (query or "").strip()
    if not client or not keyword:
        return None if not client else []

    try:
        response = client.search(
            index=DOCUMENT_INDEX,
            size=limit,
            query={
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": keyword,
                                "fields": ["title^3", "content"],
                                "type": "best_fields",
                            }
                        }
                    ],
                    "filter": [
                        {"term": {"owner_id": owner_id}},
                    ],
                }
            },
            source=False,
        )
        hits = response.get("hits", {}).get("hits", [])
        return [int(hit["_id"]) for hit in hits]
    except NotFoundError:
        current_app.logger.warning("Elasticsearch index '%s' not found", DOCUMENT_INDEX)
        return []
    except Exception as exc:  # pylint: disable=broad-except
        current_app.logger.warning("Elasticsearch search error: %s", exc)
        return None
