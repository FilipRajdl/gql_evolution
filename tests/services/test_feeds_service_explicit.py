
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

from src.DBDefinitions import FeedsModel, ComposeConnectionString
from src.Dataloaders import LoaderMap
from src.ServiceDefinitions.ServiceContext import ServiceContext


@pytest.mark.explicit
@pytest.mark.asyncio
async def test_feeds_service_crud():

    engine = create_async_engine(
        ComposeConnectionString()
    )

    session_maker = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    feed_id = uuid.uuid4()
    owner_id = uuid.uuid4()

    try:
        async with session_maker() as session:
            ctx = ServiceContext(
                loaders=LoaderMap(session),
                session=session,
                user={"id": str(owner_id)},
            )


            service = ctx.Services.FeedsService

            try:
                # CREATE
                created = await service.Create(
                    ctx=ctx,
                    entity=FeedsModel(
                        id=feed_id,
                        name="Pytest feed",
                        description="Integracni test",
                        color="#3498db",
                    ),
                )

                assert created is not None
                assert created.id == feed_id
                assert created.owner_id == owner_id

                # READ
                loaded = await service.ReadById(
                    ctx=ctx,
                    id=feed_id,
                )

                assert loaded is not None
                assert loaded.name == "Pytest feed"

                # UPDATE
                updated = await service.Update(
                    ctx=ctx,
                    entity=FeedsModel(
                        id=feed_id,
                        lastchange=loaded.lastchange,
                        name="Upraveny pytest feed",
                        description="Integracni test",
                        color="#3498db",
                    ),
                )

                assert updated is not None
                assert updated.name == "Upraveny pytest feed"
                assert updated.owner_id == owner_id

                await session.flush()

                # Overeni skutecne hodnoty v databazi
                db_name = await session.scalar(
                    select(FeedsModel.name).where(
                        FeedsModel.id == feed_id
                    )
                )

                assert db_name == "Upraveny pytest feed"

                # DELETE
                await service.Delete(
                    ctx=ctx,
                    entity=updated,
                )

                # Overeni smazani
                deleted = await session.scalar(
                    select(FeedsModel).where(
                        FeedsModel.id == feed_id
                    )
                )

                assert deleted is None

            finally:
                await session.rollback()

    finally:
        await engine.dispose()
