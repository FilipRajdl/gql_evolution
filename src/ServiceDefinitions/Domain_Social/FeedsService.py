
from uoishelpers.dataloaders.IDLoader import IDLoader

from src.DBDefinitions import FeedsModel
from src.ServiceDefinitions.BaseService import BaseService
from src.ServiceDefinitions.ServiceContext import ServiceContext


class FeedsService(BaseService[IDLoader[FeedsModel]]):
    """Sluzba pro spravu uzivatelskych feedu."""

    @classmethod
    async def getLoader(cls, ctx: ServiceContext) -> IDLoader[FeedsModel]:
        return ctx.loaders.FeedsModel
