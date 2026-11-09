
from uoishelpers.dataloaders.IDLoader import IDLoader

from src.DBDefinitions import FeedsTypeModel
from src.ServiceDefinitions.BaseService import BaseService
from src.ServiceDefinitions.ServiceContext import ServiceContext


class FeedsTypeService(BaseService[IDLoader[FeedsTypeModel]]):
    """Sluzba pro spravu stromoveho ciselniku typu feedu."""

    @classmethod
    async def getLoader(cls, ctx: ServiceContext) -> IDLoader[FeedsTypeModel]:
        return ctx.loaders.FeedsTypeModel
