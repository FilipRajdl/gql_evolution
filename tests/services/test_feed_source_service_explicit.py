
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

@pytest.mark.explicit
@pytest.mark.asyncio
async def test_read_page_only_returns_owned_records():
    engine = create_async_engine(ComposeConnectionString())
    session_maker = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    owner_id = uuid.uuid4()
    other_id = uuid.uuid4()

    own_feed_id = uuid.uuid4()
    foreign_feed_id = uuid.uuid4()

    own_source_id = uuid.uuid4()
    foreign_source_id = uuid.uuid4()
    inconsistent_source_id = uuid.uuid4()

    try:
        async with session_maker() as session:
            try:
                own_feed = FeedsModel(
                    id=own_feed_id,
                    name="Muj testovaci feed",
                    owner_id=owner_id,
                )

                foreign_feed = FeedsModel(
                    id=foreign_feed_id,
                    name="Cizi testovaci feed",
                    owner_id=other_id,
                )

                session.add_all([own_feed, foreign_feed])
                await session.flush()

                sources = [
                    FeedSourceModel(
                        id=own_source_id,
                        feed_id=own_feed_id,
                        entity_id=uuid.uuid4(),
                        entity_type_id=uuid.uuid4(),
                        owner_id=owner_id,
                    ),
                    FeedSourceModel(
                        id=foreign_source_id,
                        feed_id=foreign_feed_id,
                        entity_id=uuid.uuid4(),
                        entity_type_id=uuid.uuid4(),
                        owner_id=other_id,
                    ),
                    # Simulace starsich nekonzistentnich dat:
                    # zdroj ma naseho vlastnika, ale cizi feed.
                    FeedSourceModel(
                        id=inconsistent_source_id,
                        feed_id=foreign_feed_id,
                        entity_id=uuid.uuid4(),
                        entity_type_id=uuid.uuid4(),
                        owner_id=owner_id,
                    ),
                ]

                session.add_all(sources)
                await session.flush()

                ctx = ServiceContext(
                    loaders=LoaderMap(session),
                    session=session,
                    user={"id": str(owner_id)},
                )

                feed_rows = await ctx.Services.FeedsService.ReadPage(
                    ctx=ctx,
                    limit=100,
                    where={
                        "id": {
                            "_in": [own_feed_id, foreign_feed_id]
                        }
                    },
                )

                assert {row.id for row in feed_rows} == {
                    own_feed_id
                }

                source_rows = await ctx.Services.FeedSourceService.ReadPage(
                    ctx=ctx,
                    limit=100,
                    where={
                        "id": {
                            "_in": [
                                own_source_id,
                                foreign_source_id,
                                inconsistent_source_id,
                            ]
                        }
                    },
                )

                assert {row.id for row in source_rows} == {
                    own_source_id
                }

            finally:
                await session.rollback()

    finally:
        await engine.dispose()

