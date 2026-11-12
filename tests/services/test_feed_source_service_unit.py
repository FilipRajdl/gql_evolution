
import types
import uuid

import pytest

from src.ServiceDefinitions.BaseService import ServiceExceptionWithCode
from src.ServiceDefinitions.Domain_Social.FeedSourceService import FeedSourceService
from src.ServiceDefinitions.Domain_Social.errors import (
    FEED_SOURCE_NOT_FOUND,
    FEED_SOURCE_NOT_OWNER,
)

class FakeSourceLoader:
    
    def __init__(self, sources=None):
        self.sources = sources or {}
        self.updated_entities = []
        self.deleted_ids = []


    async def load(self, id_):
        return self.sources.get(id_)

    async def filter_by(self, **kwargs):
        feed_id = kwargs.get("feed_id")

        return (
            source
            for source in self.sources.values()
            if source.feed_id == feed_id
        )
    
    async def update(self, *, entity, **kwargs):
        self.updated_entities.append(entity)
        return entity

    async def delete(self, id_):
        self.deleted_ids.append(id_)
        return None
    


def _ctx(loader, user=None):
    return types.SimpleNamespace(
        user=user,
        loaders=types.SimpleNamespace(
            FeedSourceModel=loader
        ),
    )


@pytest.mark.asyncio
async def test_owner_can_access_source():
    owner_id = uuid.uuid4()
    source_id = uuid.uuid4()

    source = types.SimpleNamespace(
        id=source_id,
        owner_id=owner_id,
    )

    loader = FakeSourceLoader(
        sources={source_id: source}
    )

    result = await FeedSourceService.EnsureUserIsOwnerForSource(
        ctx=_ctx(loader, user={"id": str(owner_id)}),
        source_id=str(source_id),
    )

    assert result is source


@pytest.mark.asyncio
async def test_other_user_cannot_access_source():
    source_id = uuid.uuid4()

    source = types.SimpleNamespace(
        id=source_id,
        owner_id=uuid.uuid4(),
    )

    loader = FakeSourceLoader(
        sources={source_id: source}
    )

    with pytest.raises(ServiceExceptionWithCode) as exc_info:
        await FeedSourceService.EnsureUserIsOwnerForSource(
            ctx=_ctx(loader, user={"id": str(uuid.uuid4())}),
            source_id=source_id,
        )

    assert exc_info.value.code == FEED_SOURCE_NOT_OWNER



@pytest.mark.asyncio
async def test_missing_source():
    loader = FakeSourceLoader()

    with pytest.raises(ServiceExceptionWithCode) as exc_info:
        await FeedSourceService.EnsureUserIsOwnerForSource(
            ctx=_ctx(loader),
            source_id=uuid.uuid4(),
        )

    assert exc_info.value.code == FEED_SOURCE_NOT_FOUND


@pytest.mark.asyncio
async def test_get_sources_for_feed():
    feed_id = uuid.uuid4()

    source1 = types.SimpleNamespace(
        id=uuid.uuid4(),
        feed_id=feed_id,
    )

    source2 = types.SimpleNamespace(
        id=uuid.uuid4(),
        feed_id=feed_id,
    )

    other_source = types.SimpleNamespace(
        id=uuid.uuid4(),
        feed_id=uuid.uuid4(),
    )

    loader = FakeSourceLoader(
        sources={
            source1.id: source1,
            source2.id: source2,
            other_source.id: other_source,
        }
    )

    result = await FeedSourceService.GetSourcesForFeed(
        ctx=_ctx(loader),
        feed_id=str(feed_id),
    )

    assert result == [source1, source2]


@pytest.mark.asyncio
async def test_owner_can_update_source():
    owner_id = uuid.uuid4()
    source_id = uuid.uuid4()

    source = types.SimpleNamespace(
        id=source_id,
        owner_id=owner_id,
    )

    loader = FakeSourceLoader(
        sources={source_id: source}
    )

    entity = types.SimpleNamespace(
        id=source_id,
        entity_id=uuid.uuid4(),
    )

    result = await FeedSourceService.UpdateByOwner(
        ctx=_ctx(loader, user={"id": str(owner_id)}),
        entity=entity,
    )

    assert result is entity
    assert loader.updated_entities == [entity]


@pytest.mark.asyncio
async def test_other_user_cannot_update_source():
    source_id = uuid.uuid4()

    source = types.SimpleNamespace(
        id=source_id,
        owner_id=uuid.uuid4(),
    )

    loader = FakeSourceLoader(
        sources={source_id: source}
    )

    with pytest.raises(ServiceExceptionWithCode) as exc_info:
        await FeedSourceService.UpdateByOwner(
            ctx=_ctx(loader, user={"id": str(uuid.uuid4())}),
            entity=types.SimpleNamespace(id=source_id),
        )

    assert exc_info.value.code == FEED_SOURCE_NOT_OWNER
    assert loader.updated_entities == []


@pytest.mark.asyncio
async def test_owner_can_delete_source():
    owner_id = uuid.uuid4()
    source_id = uuid.uuid4()

    source = types.SimpleNamespace(
        id=source_id,
        owner_id=owner_id,
    )

    loader = FakeSourceLoader(
        sources={source_id: source}
    )

    result = await FeedSourceService.DeleteByOwner(
        ctx=_ctx(loader, user={"id": str(owner_id)}),
        entity=types.SimpleNamespace(id=source_id),
    )

    assert result is None
    assert loader.deleted_ids == [source_id]


@pytest.mark.asyncio
async def test_other_user_cannot_delete_source():
    source_id = uuid.uuid4()

    source = types.SimpleNamespace(
        id=source_id,
        owner_id=uuid.uuid4(),
    )

    loader = FakeSourceLoader(
        sources={source_id: source}
    )

    with pytest.raises(ServiceExceptionWithCode) as exc_info:
        await FeedSourceService.DeleteByOwner(
            ctx=_ctx(loader, user={"id": str(uuid.uuid4())}),
            entity=types.SimpleNamespace(id=source_id),
        )

    assert exc_info.value.code == FEED_SOURCE_NOT_OWNER
    assert loader.deleted_ids == []


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["Update", "Delete"])
async def test_standard_crud_rejects_other_user(method_name):
    source_id = uuid.uuid4()

    source = types.SimpleNamespace(
        id=source_id,
        owner_id=uuid.uuid4(),
    )

    loader = FakeSourceLoader(
        sources={source_id: source}
    )

    ctx = _ctx(
        loader,
        user={"id": str(uuid.uuid4())},
    )

    method = getattr(FeedSourceService, method_name)

    with pytest.raises(ServiceExceptionWithCode) as exc_info:
        await method(
            ctx=ctx,
            entity=types.SimpleNamespace(id=source_id),
        )

    assert exc_info.value.code == FEED_SOURCE_NOT_OWNER
    assert loader.updated_entities == []
    assert loader.deleted_ids == []


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["Update", "Delete"])
async def test_standard_crud_allows_owner(method_name):
    owner_id = uuid.uuid4()
    source_id = uuid.uuid4()

    source = types.SimpleNamespace(
        id=source_id,
        owner_id=owner_id,
    )

    loader = FakeSourceLoader(
        sources={source_id: source}
    )

    ctx = _ctx(
        loader,
        user={"id": str(owner_id)},
    )

    entity = types.SimpleNamespace(id=source_id)

    method = getattr(FeedSourceService, method_name)

    await method(ctx=ctx, entity=entity)

    if method_name == "Update":
        assert loader.updated_entities == [entity]

    else:
        assert loader.deleted_ids == [source_id]
