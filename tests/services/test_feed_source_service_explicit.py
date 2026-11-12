
import uuid
import types

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

from src.DBDefinitions import (
    FeedsModel,
    FeedSourceModel,
    ComposeConnectionString,
)
from src.Dataloaders import LoaderMap
from src.ServiceDefinitions.BaseService import ServiceExceptionWithCode
from src.ServiceDefinitions.ServiceContext import ServiceContext
from src.ServiceDefinitions.Domain_Social.errors import (
    FEED_SOURCE_NOT_FOUND,
    FEED_SOURCE_NOT_OWNER,
)


@pytest.mark.explicit
@pytest.mark.asyncio
async def test_feed_source_service_explicit():

    engine = create_async_engine(
        ComposeConnectionString()
    )

    session_maker = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    owner_id = uuid.uuid4()
    feed_id = uuid.uuid4()
    source_id = uuid.uuid4()

    try:
        async with session_maker() as session:

            ctx = ServiceContext(
                loaders=LoaderMap(session),
                session=session,
                user={"id": str(owner_id)},
            )

            feed_service = ctx.Services.FeedsService
            source_service = ctx.Services.FeedSourceService

            try:
                # 1. Vytvoreni feedu
                await feed_service.Create(
                    ctx=ctx,
                    entity=FeedsModel(
                        id=feed_id,
                        name="Pytest feed",
                        owner_id=owner_id,
                    ),
                )

                # 2. Vytvoreni zdroje
                source = await source_service.Create(
                    ctx=ctx,
                    entity=FeedSourceModel(
                        id=source_id,
                        feed_id=feed_id,
                        entity_id=uuid.uuid4(),
                        entity_type_id=uuid.uuid4(),
                        owner_id=owner_id,
                    ),
                )

                assert source.id == source_id
                assert source.feed_id == feed_id

                # 3. Nacteni zdroju feedu
                sources = await source_service.GetSourcesForFeed(
                    ctx=ctx,
                    feed_id=feed_id,
                )

                assert len(sources) == 1
                assert sources[0].id == source_id

                # 4. Cizi uzivatel nesmi zdroj upravit
                ctx.user = {"id": str(uuid.uuid4())}

                with pytest.raises(ServiceExceptionWithCode) as exc:
                    await source_service.UpdateByOwner(
                        ctx=ctx,
                        entity=types.SimpleNamespace(
                            id=source_id,
                        ),
                    )

                assert exc.value.code == FEED_SOURCE_NOT_OWNER

                # 5. Vlastnik muze zdroj upravit
                ctx.user = {"id": str(owner_id)}

                new_entity_id = uuid.uuid4()

                updated = await source_service.UpdateByOwner(
                    ctx=ctx,
                    entity=types.SimpleNamespace(
                        id=source_id,
                        lastchange=source.lastchange,
                        entity_id=new_entity_id,
                    ),
                )

                assert updated is not None
                assert updated.entity_id == new_entity_id

                await session.flush()

                db_entity_id = await session.scalar(
                    select(FeedSourceModel.entity_id).where(
                        FeedSourceModel.id == source_id
                    )
                )

                assert db_entity_id == new_entity_id

                # 6. Vlastnik muze zdroj smazat
                await source_service.DeleteByOwner(
                    ctx=ctx,
                    entity=updated,
                )

                deleted = await session.scalar(
                    select(FeedSourceModel).where(
                        FeedSourceModel.id == source_id
                    )
                )

                assert deleted is None

                # 7. Smazani testovaciho feedu
                await feed_service.Delete(
                    ctx=ctx,
                    entity=types.SimpleNamespace(
                        id=feed_id,
                    ),
                )

            finally:
                await session.rollback()

    finally:
        await engine.dispose()
