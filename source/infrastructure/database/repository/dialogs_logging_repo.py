from sqlalchemy.ext.asyncio import AsyncSession

from source.infrastructure.database.models.user_model import UserDialogsLogging
from source.infrastructure.database.repository.base_repo import BaseRepository


class UserDialogsLoggingRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(model=UserDialogsLogging, session=session)