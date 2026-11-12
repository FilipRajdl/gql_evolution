
import uuid

from uoishelpers.dataloaders.IDLoader import IDLoader

from src.DBDefinitions import FeedsModel
from src.ServiceDefinitions.BaseService import (
    BaseService,
    ServiceExceptionWithCode,
)
from src.ServiceDefinitions.ServiceContext import ServiceContext

from .errors import (
    FEED_NOT_FOUND,
    FEED_NOT_OWNER,
    FEED_USER_REQUIRED,
    ERROR_MESSAGES,
)


class FeedsService(BaseService[IDLoader[FeedsModel]]):

    @classmethod
    async def getLoader(cls, ctx: ServiceContext) -> IDLoader[FeedsModel]:
        return ctx.loaders.FeedsModel

    @classmethod
    def _get_user_id(cls, ctx: ServiceContext):
        user_id = (
            ctx.user.get("id")
            if isinstance(ctx.user, dict)
            else getattr(ctx.user, "id", None)
        )

        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        if user_id is None:
            raise ServiceExceptionWithCode(
                ERROR_MESSAGES[FEED_USER_REQUIRED],
                code=FEED_USER_REQUIRED,
                location="FeedsService",
            )

        return user_id

    @classmethod
    async def EnsureUserIsOwnerForFeed(cls, ctx, feed_id):
        user_id = cls._get_user_id(ctx)

        if isinstance(feed_id, str):
            feed_id = uuid.UUID(feed_id)

        loader = await cls.getLoader(ctx)
        feed = await loader.load(feed_id)

        if feed is None:
            raise ServiceExceptionWithCode(
                ERROR_MESSAGES[FEED_NOT_FOUND],
                code=FEED_NOT_FOUND,
                location="EnsureUserIsOwnerForFeed",
            )

        if feed.owner_id != user_id:
            raise ServiceExceptionWithCode(
                ERROR_MESSAGES[FEED_NOT_OWNER],
                code=FEED_NOT_OWNER,
                location="EnsureUserIsOwnerForFeed",
            )

        return feed

    
    @classmethod
    async def ReadById(cls, ctx, id):
        user_id = cls._get_user_id(ctx)

        if isinstance(id, str):
            id = uuid.UUID(id)

        loader = await cls.getLoader(ctx)
        feed = await loader.load(id)

        if feed is None:
            return None

        if feed.owner_id != user_id:
            raise ServiceExceptionWithCode(
                ERROR_MESSAGES[FEED_NOT_OWNER],
                code=FEED_NOT_OWNER,
                location="FeedsService.ReadById",
            )

        return feed    

    @classmethod
    async def Create(cls, ctx, entity, extraAttributes=None):
        user_id = cls._get_user_id(ctx)

        attributes = dict(extraAttributes or {})
        attributes["owner_id"] = user_id

        return await super().Create(
            ctx=ctx,
            entity=entity,
            extraAttributes=attributes,
        )

    @classmethod
    async def Update(cls, ctx, entity, extraValues=None):
        feed = await cls.EnsureUserIsOwnerForFeed(
            ctx=ctx,
            feed_id=entity.id,
        )

        values = dict(extraValues or {})
        values["owner_id"] = feed.owner_id
        values["id"] = feed.id

        return await super().Update(
            ctx=ctx,
            entity=entity,
            extraValues=values,
        )

    @classmethod
    async def Delete(cls, ctx, entity):
        feed = await cls.EnsureUserIsOwnerForFeed(
            ctx=ctx,
            feed_id=entity.id,
        )

        return await super().Delete(
            ctx=ctx,
            entity=feed,
        )


    @classmethod
    async def ReadPage(
        cls,
        ctx,
        skip=0,
        limit=10,
        where=None,
        orderby=None,
        desc=None,
        extendedfilter=None,
    ):
        user_id = cls._get_user_id(ctx)

        filters = dict(extendedfilter or {})
        filters["owner_id"] = user_id

        return await super().ReadPage(
            ctx=ctx,
            skip=skip,
            limit=limit,
            where=where,
            orderby=orderby,
            desc=desc,
            extendedfilter=filters,
        )
