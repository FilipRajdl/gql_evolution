
import types
import uuid

import pytest

from src.ServiceDefinitions.Domain_Social.FeedsService import FeedsService
from src.ServiceDefinitions.BaseService import ServiceExceptionWithCode
from src.ServiceDefinitions.Domain_Social.errors import (
    FEED_NOT_FOUND,
    FEED_NOT_OWNER,
    FEED_USER_REQUIRED,
)


class FakeFeedLoader:
    def __init__(self):
        self.feeds = {}

    async def insert(self, *, entity, extraAttributes=None):
        for key, value in (extraAttributes or {}).items():
            setattr(entity, key, value)

        self.feeds[entity.id] = entity
        return entity

    async def load(self, id_):
        return self.feeds.get(id_)

    async def page(self, **kwargs):
        return list(self.feeds.values())

    async def update(self, *, entity, extraValues=None):
        for key, value in (extraValues or {}).items():
            setattr(entity, key, value)

        self.feeds[entity.id] = entity
        return entity

    async def delete(self, id_):
        self.feeds.pop(id_, None)
        return None


def _ctx(loader, user=None):
    return types.SimpleNamespace(
        user=user,
        loaders=types.SimpleNamespace(
            FeedsModel=loader
        ),
    )


@pytest.mark.asyncio
async def test_create_feed():
    loader = FakeFeedLoader()
    owner_id = uuid.uuid4()
    ctx = _ctx(loader, user={"id": str(owner_id)})

    entity = types.SimpleNamespace(
        id=None,
        name="Moje projekty",
        owner_id=uuid.uuid4(),
    )

    result = await FeedsService.Create(
        ctx=ctx,
        entity=entity,
    )

    assert result.id is not None
    assert result.name == "Moje projekty"
    assert result.owner_id == owner_id
    assert loader.feeds[result.id] is result


@pytest.mark.asyncio
async def test_read_feed():
    loader = FakeFeedLoader()
    owner_id = uuid.uuid4()
    ctx = _ctx(loader, user={"id": str(owner_id)})

    feed = types.SimpleNamespace(
        id=uuid.uuid4(),
        name="Moje projekty",
        owner_id=owner_id,
    )

    loader.feeds[feed.id] = feed

    result = await FeedsService.ReadById(
        ctx=ctx,
        id=feed.id,
    )

    assert result is feed
    assert await FeedsService.ReadPage(ctx=ctx) == [feed]


@pytest.mark.asyncio
async def test_update_and_delete_feed():
    loader = FakeFeedLoader()
    owner_id = uuid.uuid4()
    ctx = _ctx(loader, user={"id": str(owner_id)})

    feed = types.SimpleNamespace(
        id=uuid.uuid4(),
        name="Puvodni nazev",
        owner_id=owner_id,
    )

    loader.feeds[feed.id] = feed

    updated = types.SimpleNamespace(
        id=feed.id,
        name="Novy nazev",
        owner_id=uuid.uuid4(),
    )

    result = await FeedsService.Update(
        ctx=ctx,
        entity=updated,
    )

    assert result.name == "Novy nazev"
    assert result.owner_id == owner_id

    await FeedsService.Delete(
        ctx=ctx,
        entity=result,
    )

    assert await FeedsService.ReadById(
        ctx=ctx,
        id=feed.id,
    ) is None


@pytest.mark.asyncio
async def test_create_requires_user():
    loader = FakeFeedLoader()
    ctx = _ctx(loader)

    with pytest.raises(ServiceExceptionWithCode) as exc:
        await FeedsService.Create(
            ctx=ctx,
            entity=types.SimpleNamespace(
                id=None,
                name="Test feed",
            ),
        )

    assert exc.value.code == FEED_USER_REQUIRED
    assert loader.feeds == {}


@pytest.mark.asyncio
async def test_missing_feed():
    loader = FakeFeedLoader()
    ctx = _ctx(
        loader,
        user={"id": str(uuid.uuid4())},
    )

    with pytest.raises(ServiceExceptionWithCode) as exc:
        await FeedsService.EnsureUserIsOwnerForFeed(
            ctx=ctx,
            feed_id=str(uuid.uuid4()),
        )

    assert exc.value.code == FEED_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["Update", "Delete"])
async def test_other_user_cannot_modify_feed(method_name):
    loader = FakeFeedLoader()

    feed = types.SimpleNamespace(
        id=uuid.uuid4(),
        name="Cizi feed",
        owner_id=uuid.uuid4(),
    )

    loader.feeds[feed.id] = feed

    ctx = _ctx(
        loader,
        user={"id": str(uuid.uuid4())},
    )

    method = getattr(FeedsService, method_name)

    with pytest.raises(ServiceExceptionWithCode) as exc:
        await method(
            ctx=ctx,
            entity=types.SimpleNamespace(id=feed.id),
        )

    assert exc.value.code == FEED_NOT_OWNER
    assert loader.feeds[feed.id] is feed
    assert feed.name == "Cizi feed"
