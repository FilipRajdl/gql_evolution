from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.DBDefinitions.BaseModel import BaseDBModel, IDType


class FeedSourceModel(BaseDBModel):
    """Source of activities tracked in a user's feed."""

    __tablename__ = "feed_sources"

    # Feed to which the tracked entity belongs.
    feed_id: Mapped[IDType] = mapped_column(
        ForeignKey("feeds.id"),
        index=True,
        nullable=False,
        kw_only=True,
        comment="ID of the feed that contains this source",
    )

    # UUID of the tracked entity (e.g. project or grant).
    entity_id: Mapped[IDType] = mapped_column(
        index=True,
        nullable=False,
        kw_only=True,
        comment="ID of the tracked entity",
    )

    # Specifies what kind of entity entity_id identifies.
    # Do not reference feedtypes here: a feed type and a tracked-entity type
    # are not necessarily the same catalog.
    entity_type_id: Mapped[IDType] = mapped_column(
        index=True,
        nullable=False,
        kw_only=True,
        comment="ID of the tracked entity type",
    )

    # Owner of this feed source's settings.
    owner_id: Mapped[IDType] = mapped_column(
        index=True,
        nullable=False,
        kw_only=True,
        comment="ID of the user who owns this source setting",
    )

    # The feed is a local SQLAlchemy model, so this relationship is safe.
    # Other tracked entity types may belong to external services.
    feed = relationship(
        "FeedsModel",
        uselist=False,
        viewonly=True,
        init=False,
    )
