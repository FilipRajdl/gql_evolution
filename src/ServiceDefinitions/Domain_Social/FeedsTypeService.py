import uuid
from uoishelpers.dataloaders.IDLoader import IDLoader

from src.DBDefinitions import FeedsTypeModel
from src.ServiceDefinitions.BaseService import BaseService
from src.ServiceDefinitions.ServiceContext import ServiceContext


class FeedsTypeService(BaseService[IDLoader[FeedsTypeModel]]):
    """Sluzba pro spravu stromoveho ciselniku typu feedu."""

    @classmethod
    async def getLoader(cls, ctx: ServiceContext) -> IDLoader[FeedsTypeModel]:
        return ctx.loaders.FeedsTypeModel

    
    @classmethod
    async def GetChildrenForType(cls, ctx: ServiceContext, parent_id):
        loader = await cls.getLoader(ctx)

        if isinstance(parent_id, str):
            parent_id = uuid.UUID(parent_id)

        children = await loader.filter_by(parent_id=parent_id)
        return list(children)
    
