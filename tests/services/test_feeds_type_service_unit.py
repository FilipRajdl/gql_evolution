
import types
import uuid

import pytest

from src.ServiceDefinitions.Domain_Social.FeedsTypeService import FeedsTypeService


class FakeTypeLoader:
    def __init__(self, types_data=None):
        self.types_data = types_data or []

    async def filter_by(self, **kwargs):
        parent_id = kwargs.get("parent_id")

        return (
            item
            for item in self.types_data
            if item.parent_id == parent_id
        )


def _ctx(loader):
    return types.SimpleNamespace(
        loaders=types.SimpleNamespace(
            FeedsTypeModel=loader
        ),
    )


@pytest.mark.asyncio
async def test_get_children_for_type():
    parent_id = uuid.uuid4()

    child1 = types.SimpleNamespace(
        id=uuid.uuid4(),
        name="Projektove feedy",
        parent_id=parent_id,
    )

    child2 = types.SimpleNamespace(
        id=uuid.uuid4(),
        name="Grantove feedy",
        parent_id=parent_id,
    )

    other_child = types.SimpleNamespace(
        id=uuid.uuid4(),
        name="Fakultni feedy",
        parent_id=uuid.uuid4(),
    )

    loader = FakeTypeLoader(
        types_data=[child1, child2, other_child]
    )

    result = await FeedsTypeService.GetChildrenForType(
        ctx=_ctx(loader),
        parent_id=str(parent_id),
    )

    assert result == [child1, child2]


@pytest.mark.asyncio
async def test_type_without_children():
    loader = FakeTypeLoader()

    result = await FeedsTypeService.GetChildrenForType(
        ctx=_ctx(loader),
        parent_id=uuid.uuid4(),
    )

    assert result == []
