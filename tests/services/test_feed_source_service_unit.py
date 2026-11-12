
import types
import uuid

import pytest

from src.ServiceDefinitions.BaseService import ServiceExceptionWithCode
from src.ServiceDefinitions.Domain_Social.FeedSourceService import FeedSourceService
from src.ServiceDefinitions.Domain_Social.errors import (
    FEED_SOURCE_NOT_FOUND,
    FEED_SOURCE_NOT_OWNER,
    FEED_NOT_OWNER,
    FEED_USER_REQUIRED,
    FEED_SOURCE_IMMUTABLE,
    FEED_NOT_OWNER,
)
from src.ServiceDefinitions.ServiceContext import ServiceContext

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

    
    async def insert(self, *, entity, extraAttributes=None):
        for key, value in (extraAttributes or {}).items():
            setattr(entity, key, value)

        self.sources[entity.id] = entity
        return entity
    
    


def _ctx(loader, user=None):
    # Pro stare jednotkove testy pripravime
    # ke kazdemu zdroji odpovidajici feed.
    feeds = {}

    for source in loader.sources.values():
        feed_id = getattr(source, "feed_id", None)

        if feed_id is None:
            feed_id = uuid.uuid4()
            source.feed_id = feed_id

        feeds[feed_id] = types.SimpleNamespace(
            id=feed_id,
            owner_id=getattr(source, "owner_id", None),
        )

    return ServiceContext(
        user=user,
        loaders=types.SimpleNamespace(
            FeedSourceModel=loader,
            FeedsModel=FakeSourceLoader(sources=feeds),
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
    owner_id = uuid.uuid4()
    feed_id = uuid.uuid4()

    feed = types.SimpleNamespace(
        id=feed_id,
        owner_id=owner_id,
    )

    source1 = types.SimpleNamespace(
        id=uuid.uuid4(),
        feed_id=feed_id,
        owner_id=owner_id,
    )

    source2 = types.SimpleNamespace(
        id=uuid.uuid4(),
        feed_id=feed_id,
        owner_id=owner_id,
    )

    inconsistent_source = types.SimpleNamespace(
        id=uuid.uuid4(),
        feed_id=feed_id,
        owner_id=uuid.uuid4(),
    )

    other_source = types.SimpleNamespace(
        id=uuid.uuid4(),
        feed_id=uuid.uuid4(),
    )

    feed_loader = FakeSourceLoader(
        sources={feed_id: feed}
    )

    source_loader = FakeSourceLoader(
        sources={
            source1.id: source1,
            source2.id: source2,
            other_source.id: other_source,
            inconsistent_source.id: inconsistent_source,
        }
    )

    ctx = ServiceContext(
        loaders=types.SimpleNamespace(
            FeedsModel=feed_loader,
            FeedSourceModel=source_loader,
        ),
        user={"id": str(owner_id)},
    )

    result = await FeedSourceService.GetSourcesForFeed(
        ctx=ctx,
        feed_id=str(feed_id),
    )

    assert result == [source1, source2]


@pytest.mark.asyncio
async def test_other_user_cannot_get_sources_for_feed():
    feed_id = uuid.uuid4()

    feed = types.SimpleNamespace(
        id=feed_id,
        owner_id=uuid.uuid4(),
    )

    feed_loader = FakeSourceLoader(
        sources={feed_id: feed}
    )

    source_loader = FakeSourceLoader()

    ctx = ServiceContext(
        loaders=types.SimpleNamespace(
            FeedsModel=feed_loader,
            FeedSourceModel=source_loader,
        ),
        user={"id": str(uuid.uuid4())},
    )

    with pytest.raises(ServiceExceptionWithCode) as exc:
        await FeedSourceService.GetSourcesForFeed(
            ctx=ctx,
            feed_id=feed_id,
        )

    assert exc.value.code == FEED_NOT_OWNER


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_type",
    ["owner", "other", "anonymous"],
)
async def test_create_source_permissions(user_type):
    owner_id = uuid.uuid4()
    feed_id = uuid.uuid4()

    feed = types.SimpleNamespace(
        id=feed_id,
        owner_id=owner_id,
    )

    feed_loader = FakeSourceLoader(
        sources={feed_id: feed}
    )

    source_loader = FakeSourceLoader()

    if user_type == "owner":
        user = {"id": str(owner_id)}
    elif user_type == "other":
        user = {"id": str(uuid.uuid4())}
    else:
        user = None

    ctx = ServiceContext(
        loaders=types.SimpleNamespace(
            FeedsModel=feed_loader,
            FeedSourceModel=source_loader,
        ),
        user=user,
    )

    entity = types.SimpleNamespace(
        id=None,
        feed_id=feed_id,
        entity_id=uuid.uuid4(),
        entity_type_id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
    )

    if user_type == "owner":
        result = await FeedSourceService.Create(
            ctx=ctx,
            entity=entity,
        )

        assert result.owner_id == owner_id
        assert result.feed_id == feed_id
        assert result.id is not None
        assert result.id in source_loader.sources

    else:
        with pytest.raises(ServiceExceptionWithCode) as exc:
            await FeedSourceService.Create(
                ctx=ctx,
                entity=entity,
            )

        if user_type == "other":
            assert exc.value.code == FEED_NOT_OWNER
        else:
            assert exc.value.code == FEED_USER_REQUIRED

        assert source_loader.sources == {}

@pytest.mark.asyncio
@pytest.mark.parametrize("field_name", ["owner_id", "feed_id"])
@pytest.mark.parametrize("input_location", ["entity", "extraValues"])
async def test_update_cannot_change_owner_or_feed(
    field_name,
    input_location,
):
    owner_id = uuid.uuid4()
    feed_id = uuid.uuid4()
    source_id = uuid.uuid4()

    source = types.SimpleNamespace(
        id=source_id,
        owner_id=owner_id,
        feed_id=feed_id,
    )

    loader = FakeSourceLoader(
        sources={source_id: source}
    )

    ctx = _ctx(
        loader,
        user={"id": str(owner_id)},
    )

    entity = types.SimpleNamespace(
        id=source_id,
        entity_id=uuid.uuid4(),
    )

    extra_values = {}

    if input_location == "entity":
        setattr(entity, field_name, uuid.uuid4())
    else:
        extra_values[field_name] = uuid.uuid4()

    with pytest.raises(ServiceExceptionWithCode) as exc:
        await FeedSourceService.Update(
            ctx=ctx,
            entity=entity,
            extraValues=extra_values,
        )

    assert exc.value.code == FEED_SOURCE_IMMUTABLE
    assert loader.updated_entities == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "foreign_part",
    ["source", "feed"],
)
async def test_cannot_read_foreign_source_by_id(foreign_part):
    owner_id = uuid.uuid4()
    feed_id = uuid.uuid4()
    source_id = uuid.uuid4()

    feed = types.SimpleNamespace(
        id=feed_id,
        owner_id=(
            uuid.uuid4()
            if foreign_part == "feed"
            else owner_id
        ),
    )

    source = types.SimpleNamespace(
        id=source_id,
        feed_id=feed_id,
        owner_id=(
            uuid.uuid4()
            if foreign_part == "source"
            else owner_id
        ),
    )

    ctx = ServiceContext(
        loaders=types.SimpleNamespace(
            FeedsModel=FakeSourceLoader(
                sources={feed_id: feed}
            ),
            FeedSourceModel=FakeSourceLoader(
                sources={source_id: source}
            ),
        ),
        user={"id": str(owner_id)},
    )

    with pytest.raises(ServiceExceptionWithCode) as exc:
        await FeedSourceService.ReadById(
            ctx=ctx,
            id=str(source_id),
        )

    expected_code = (
        FEED_SOURCE_NOT_OWNER
        if foreign_part == "source"
        else FEED_NOT_OWNER
    )

    assert exc.value.code == expected_code


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["Update", "Delete"])
async def test_cannot_modify_source_in_foreign_feed(method_name):
    owner_id = uuid.uuid4()
    feed_id = uuid.uuid4()
    source_id = uuid.uuid4()

    # Zdroj patri nasemu uzivateli.
    source = types.SimpleNamespace(
        id=source_id,
        feed_id=feed_id,
        owner_id=owner_id,
    )

    # Ale nadrazeny feed patri nekomu jinemu.
    feed = types.SimpleNamespace(
        id=feed_id,
        owner_id=uuid.uuid4(),
    )

    source_loader = FakeSourceLoader(
        sources={source_id: source}
    )

    feed_loader = FakeSourceLoader(
        sources={feed_id: feed}
    )

    ctx = ServiceContext(
        loaders=types.SimpleNamespace(
            FeedsModel=feed_loader,
            FeedSourceModel=source_loader,
        ),
        user={"id": str(owner_id)},
    )

    method = getattr(FeedSourceService, method_name)

    with pytest.raises(ServiceExceptionWithCode) as exc:
        await method(
            ctx=ctx,
            entity=types.SimpleNamespace(id=source_id),
        )

    assert exc.value.code == FEED_NOT_OWNER
    assert source_loader.updated_entities == []
    assert source_loader.deleted_ids == []
