from fastapi import APIRouter, Depends, status, HTTPException
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.database import get_db_session
from app.api.schemas.user import UserPostRequest, UserResponse, UserPatchRequest
from app.api.schemas.base import PaginatedResponse
from app.data.models.user import User
from app.data.repositories.user import UserRepository
from app.api.pagination import get_pagination_params, PaginationParams, paginate

logger = structlog.get_logger(__name__)
user_router = APIRouter(prefix='/user')


@user_router.post(
    path='/',
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def post_user(
    user_data: UserPostRequest,
    session: AsyncSession = Depends(get_db_session)
) -> User:
    repo = UserRepository(session)
    return await repo.create_record(user_data.model_dump(), commit=True)


@user_router.get(
    path='/',
    response_model=PaginatedResponse[UserResponse],
    status_code=status.HTTP_200_OK
)
async def get_users(
    session: AsyncSession = Depends(get_db_session),
    pagination_params: PaginationParams = Depends(get_pagination_params)
) -> dict:
    repo = UserRepository(session)
    records = await repo.read_records(
        limit=pagination_params.page_size,
        offset=pagination_params.offset
    )
    count = await repo.count_records()
    return paginate(records, count, pagination_params)


@user_router.get(
    path='/{user_id}',
    response_model=UserResponse,
    status_code=status.HTTP_200_OK
)
async def get_user(
    user_id: str,
    session: AsyncSession = Depends(get_db_session)
) -> User:
    repo = UserRepository(session)
    user = await repo.read_record(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f'User {user_id} not found'
        )
    return user


@user_router.delete(
    path='/{user_id}',
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(
    user_id: str,
    session: AsyncSession = Depends(get_db_session)
) -> None:
    repo = UserRepository(session)
    deleted = await repo.delete_record(user_id, commit=True)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'User {user_id} not found',
        )


@user_router.patch(
    path='/{user_id}',
    response_model=UserResponse,
    status_code=status.HTTP_200_OK
)
async def patch_user(
    user_id: str,
    user_data: UserPatchRequest,
    session: AsyncSession = Depends(get_db_session)
) -> User:
    repo = UserRepository(session)
    user = await repo.update_record(user_id, user_data.model_dump(), commit=True)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f'User {user_id} not found'
        )
    return user
