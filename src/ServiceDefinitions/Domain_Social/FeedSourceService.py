
import uuid

from uoishelpers.dataloaders.IDLoader import IDLoader

from src.DBDefinitions import FeedSourceModel
from src.ServiceDefinitions.BaseService import (
    BaseService,
    ServiceExceptionWithCode,
)
from src.ServiceDefinitions.ServiceContext import ServiceContext

from .errors import (
    FEED_SOURCE_NOT_FOUND,
    FEED_SOURCE_NOT_OWNER,
    ERROR_MESSAGES,
)



class FeedSourceService(BaseService[IDLoader[FeedSourceModel]]):

    @classmethod
    async def getLoader(cls, ctx: ServiceContext) -> IDLoader[FeedSourceModel]:
        return ctx.loaders.FeedSourceModel

    
    @classmethod
    async def EnsureUserIsOwnerForSource(cls, ctx: ServiceContext, source_id):
        loader = await cls.getLoader(ctx)

        # Prevod ID z textu na UUID
        if isinstance(source_id, str):
            source_id = uuid.UUID(source_id)

        source = await loader.load(source_id)

        
        if source is None:
            raise ServiceExceptionWithCode(
                ERROR_MESSAGES[FEED_SOURCE_NOT_FOUND],
                code=FEED_SOURCE_NOT_FOUND,
                location="EnsureUserIsOwnerForSource",
            )


        user_id = (
            ctx.user.get("id")
            if isinstance(ctx.user, dict)
            else getattr(ctx.user, "id", None)
        )

        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        
        if user_id is None or user_id != source.owner_id:
            raise ServiceExceptionWithCode(
                ERROR_MESSAGES[FEED_SOURCE_NOT_OWNER],
                code=FEED_SOURCE_NOT_OWNER,
                location="EnsureUserIsOwnerForSource",
            )

        return source


    
    @classmethod
    async def UpdateByOwner(cls, ctx: ServiceContext, entity, extraValues=None):
        loader = await cls.getLoader(ctx)

        await cls.EnsureUserIsOwnerForSource(
            ctx=ctx,
            source_id=entity.id,
        )

        return await loader.update(
            entity=entity,
            extraValues=extraValues or {},
        )

    @classmethod
    async def DeleteByOwner(cls, ctx: ServiceContext, entity):
        loader = await cls.getLoader(ctx)

        await cls.EnsureUserIsOwnerForSource(
            ctx=ctx,
            source_id=entity.id,
        )

        return await loader.delete(entity.id)

    @classmethod
    async def GetSourcesForFeed(cls, ctx: ServiceContext, feed_id):
        loader = await cls.getLoader(ctx)

        if isinstance(feed_id, str):
            feed_id = uuid.UUID(feed_id)

        sources = await loader.filter_by(feed_id=feed_id)
        return list(sources)

    
    @classmethod
    async def Update(cls, ctx: ServiceContext, entity, extraValues=None):
        return await cls.UpdateByOwner(
            ctx=ctx,
            entity=entity,
            extraValues=extraValues,
        )

    @classmethod
    async def Delete(cls, ctx: ServiceContext, entity):
        return await cls.DeleteByOwner(
            ctx=ctx,
            entity=entity,
        )
    
