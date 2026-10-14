import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from src.DBDefinitions.BaseModel import BaseDBModel, UUIDColumn, UUIDFKey, IDType
###########################################################################################################################
#
# zde definujte sve SQLAlchemy modely
# je-li treba, muzete definovat modely obsahujici jen id polozku, na ktere se budete odkazovat
#
###########################################################################################################################

class EventTypeModel(BaseDBModel):
    __tablename__ = "feedtypes"

    path_attribute_name = "path"
    parent_attribute_name = "parent"
    parent_id_attribute_name = "parent_id"
    children_attribute_name = "children"

    # Materialized path technique
    path: Mapped[str] = mapped_column(
        index=True,
        nullable=True,
        default=None,
        comment="Materialized path technique, not implemented"
    )

    name: Mapped[str] = mapped_column(default=None, nullable=True, comment="Name of the feed type")
    name_en: Mapped[str] = mapped_column(default=None, nullable=True, comment="English name of the feed type")

    parent_id: Mapped[IDType] = mapped_column(
        ForeignKey("feedtypes.id"), 
        index=True, 
        nullable=True, 
        default=None,
        comment="Parent feed type"
    )

    parent = relationship(
        "FeedsTypeModel",
        viewonly=True, 
        remote_side="FeedsTypeModel.id",
        uselist=False,
        # back_populates="children",
    ) # https://docs.sqlalchemy.org/en/20/orm/self_referential.html

    children = relationship(
        "FeedsTypeModel", 
        back_populates="parent",
        uselist=True,
        init=True, #False? -> nebude potřeba seznam children předávat do konstruktoru
        cascade="save-update"
    ) # https://docs.sqlalchemy.org/en/20/orm/self_referential.html
    # https://docs.sqlalchemy.org/en/20/_modules/examples/materialized_paths/materialized_paths.html

    events = relationship(
        "EventModel", 
        back_populates="type",
        viewonly=True
    )
