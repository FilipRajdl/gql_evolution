
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
    FEED_SOURCE_IMMUTABLE,
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
        
        # Zdroj smi spravovat jen vlastnik nadrazeneho feedu.
        await ctx.Services.FeedsService.EnsureUserIsOwnerForFeed(
            ctx=ctx,
            feed_id=source.feed_id,
        )    

        return source

    
    @classmethod
    async def ReadById(cls, ctx: ServiceContext, id):
        if isinstance(id, str):
            id = uuid.UUID(id)

        loader = await cls.getLoader(ctx)
        source = await loader.load(id)

        if source is None:
            return None

        # Uživatel musí vlastnit samotný zdroj.
        await cls.EnsureUserIsOwnerForSource(
            ctx=ctx,
            source_id=id,
        )
        
        return source

    @classmethod
    async def UpdateByOwner(cls, ctx: ServiceContext, entity, extraValues=None):
        loader = await cls.getLoader(ctx)

        source = await cls.EnsureUserIsOwnerForSource(
            ctx=ctx,
            source_id=entity.id,
        )

        values = dict(extraValues or {})

        # Vlastnika ani prirazeni do feedu nelze zmenit.
        for field in ("owner_id", "feed_id"):
            original_value = getattr(source, field, None)

            if (
                hasattr(entity, field)
                and getattr(entity, field) != original_value
            ):
                raise ServiceExceptionWithCode(
                    ERROR_MESSAGES[FEED_SOURCE_IMMUTABLE],
                    code=FEED_SOURCE_IMMUTABLE,
                    location="UpdateByOwner",
                )

            if (
                field in values
                and values[field] != original_value
            ):
                raise ServiceExceptionWithCode(
                    ERROR_MESSAGES[FEED_SOURCE_IMMUTABLE],
                    code=FEED_SOURCE_IMMUTABLE,
                    location="UpdateByOwner",
                )

        return await loader.update(
            entity=entity,
            extraValues=values,
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
        # Nejdřív zkontrolujeme, že feed patří uživateli.
        feed = await ctx.Services.FeedsService.EnsureUserIsOwnerForFeed(
            ctx=ctx,
            feed_id=feed_id,
        )

        loader = await cls.getLoader(ctx)

        
        sources = await loader.filter_by(feed_id=feed.id)

        return [
            source
            for source in sources
            if source.owner_id == feed.owner_id
        ]
    
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

    
    @classmethod
    async def Create(cls, ctx: ServiceContext, entity, extraAttributes=None):

        feed = await ctx.Services.FeedsService.EnsureUserIsOwnerForFeed(
            ctx=ctx,
            feed_id=entity.feed_id,
        )

        attributes = dict(extraAttributes or {})
        attributes["owner_id"] = feed.owner_id
        attributes["feed_id"] = feed.id

        return await super().Create(
            ctx=ctx,
            entity=entity,
            extraAttributes=attributes,
        )

    
    @classmethod
    async def ReadPage(
        cls,
        ctx: ServiceContext,
        skip=0,
        limit=10,
        where=None,
        orderby=None,
        desc=None,
        extendedfilter=None,
    ):
        user_id = ctx.Services.FeedsService._get_user_id(ctx)

        # Zdroj musi patrit uzivateli.
        filters = dict(extendedfilter or {})
        filters["owner_id"] = user_id

        # Soucasne musi uzivateli patrit i nadrazeny feed.
        feed_filter = {
            "feed": {
                "owner_id": {"_eq": user_id}
            }
        }

        if where is None:
            safe_where = feed_filter
        else:
            safe_where = {
                "_and": [
                    feed_filter,
                    where,
                ]
            }

        return await super().ReadPage(
            ctx=ctx,
            skip=skip,
            limit=limit,
            where=safe_where,
            orderby=orderby,
            desc=desc,
            extendedfilter=filters,
        )
    