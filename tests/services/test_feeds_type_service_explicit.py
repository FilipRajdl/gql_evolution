
import uuid
import types

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

from src.DBDefinitions import FeedsTypeModel, ComposeConnectionString
from src.Dataloaders import LoaderMap
from src.ServiceDefinitions.ServiceContext import ServiceContext


@pytest.mark.explicit
@pytest.mark.asyncio
async def test_feeds_type_service_explicit():

    engine = create_async_engine(
        ComposeConnectionString()
    )

    session_maker = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    parent_id = uuid.uuid4()
    child_id = uuid.uuid4()

    try:
        async with session_maker() as session:

            ctx = ServiceContext(
                loaders=LoaderMap(session),
                session=session,
            )

            service = ctx.Services.FeedsTypeService

            try:
                # 1. Vytvoreni rodice
                parent = await service.Create(
                    ctx=ctx,
                    entity=FeedsTypeModel(
                        id=parent_id,
                        name="Pytest rodic",
                        name_en="Pytest parent",
                    ),
                )

                assert parent.id == parent_id

                # 2. Vytvoreni potomka
                child = await service.Create(
                    ctx=ctx,
                    entity=FeedsTypeModel(
                        id=child_id,
                        name="Pytest potomek",
                        name_en="Pytest child",
                        parent_id=parent_id,
                    ),
                )

                assert child.parent_id == parent_id

                # 3. Nacteni potomku
                children = await service.GetChildrenForType(
                    ctx=ctx,
                    parent_id=parent_id,
                )

                assert len(children) == 1
                assert children[0].id == child_id

                # 4. Uprava potomka
                updated = await service.Update(
                    ctx=ctx,
                    entity=types.SimpleNamespace(
                        id=child_id,
                        lastchange=child.lastchange,
                        name="Upraveny potomek",
                    ),
                )

                assert updated is not None
                assert updated.name == "Upraveny potomek"
                assert updated.parent_id == parent_id

                await session.flush()

                # Overeni zmeny v databazi
                db_name = await session.scalar(
                    select(FeedsTypeModel.name).where(
                        FeedsTypeModel.id == child_id
                    )
                )

                assert db_name == "Upraveny potomek"

                # 5. Smazani potomka
                await service.Delete(
                    ctx=ctx,
                    entity=updated,
                )

                # 6. Smazani rodice
                await service.Delete(
                    ctx=ctx,
                    entity=parent,
                )

                # Overeni, ze oba zaznamy zmizely
                remaining = await session.scalars(
                    select(FeedsTypeModel).where(
                        FeedsTypeModel.id.in_(
                            [parent_id, child_id]
                        )
                    )
                )

                assert list(remaining) == []

            finally:
                await session.rollback()

    finally:
        await engine.dispose()
