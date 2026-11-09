
from uoishelpers.dataloaders.LoaderMapBase import LoaderMapBase
from uoishelpers.dataloaders.IDLoader import IDLoader

import src.DBDefinitions
from src.DBDefinitions import (
    BaseDBModel,
    EventModel,
    EventInvitationModel,
    FeedsModel,
    FeedSourceModel,
    FeedsTypeModel,
)


class LoaderMap(LoaderMapBase[BaseDBModel]):
    BaseModel = BaseDBModel

    # Puvodni modely udalosti
    EventModel: IDLoader[src.DBDefinitions.EventModel] = None
    EventInvitationModel: IDLoader[src.DBDefinitions.EventInvitationModel] = None

    # Nase modely feedu
    FeedsModel: IDLoader[src.DBDefinitions.FeedsModel] = None
    FeedSourceModel: IDLoader[src.DBDefinitions.FeedSourceModel] = None
    FeedsTypeModel: IDLoader[src.DBDefinitions.FeedsTypeModel] = None

    def __init__(self, session):
        super().__init__(session)

        # Puvodni loadery
        self.EventModel = self.get(EventModel)
        self.EventInvitationModel = self.get(EventInvitationModel)

        # Nase loadery
        self.FeedsModel = self.get(FeedsModel)
        self.FeedSourceModel = self.get(FeedSourceModel)
        self.FeedsTypeModel = self.get(FeedsTypeModel)

    def get_by_name(self, name: str):
        return getattr(self, name)


def createLoadersContext(session):
    return {"loaders": LoaderMap(session)}
