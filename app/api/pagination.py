from dataclasses import dataclass
from fastapi import Query, HTTPException

from app.core.config import get_config

config = get_config()


@dataclass
class PaginationParams:
    """Pagination parameters extracted from query"""
    page: int
    page_size: int
    offset: int


def get_pagination_params(
    page: int = Query(1, ge=1, description='Page number'),
    page_size: int = Query(config.default_page_size, ge=1, le=100, description='Records per page')
) -> PaginationParams:
    """
    Extract pagination parameters from request query.
    """
    return PaginationParams(
        page=page,
        page_size=page_size,
        offset=(page - 1) * page_size
    )


def paginate(
    records: list,
    total_records: int,
    params: PaginationParams
) -> dict:
    """
    Helper function to structure paginated responses.
    Wraps core response data in a `content` envelope and adds pagination info
    """
    from math import ceil
    total_pages = ceil(total_records / params.page_size) if total_records > 0 else 0
    if params.page > 1 and params.page > total_pages:
        if total_pages == 1:
            total_page_clause = 'There is only 1 page.'
        else:
            total_page_clause = f'There are only {total_pages} pages.'
        raise HTTPException(
            status_code=422,
            detail=(
                f'The requested page number {params.page} is out of scope. {total_page_clause}'
            )
        )
    return {
        'content': records,
        'content_size': len(records),
        'total_records': total_records,
        'page_number': params.page,
        'page_size': params.page_size,
        'total_pages': total_pages,
        'has_next': params.page < total_pages,
        'has_previous': params.page > 1
    }
