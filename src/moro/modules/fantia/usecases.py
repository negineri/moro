"""Usecases for Fantia module."""

from dataclasses import dataclass

from injector import inject

from moro.modules.fantia.domain import (
    FantiaFanclub,
    FantiaFanclubRepository,
    FantiaPostData,
    FantiaPostRepository,
)


@inject
@dataclass
class FantiaGetFanclubUseCase:
    """Use case for getting a Fantia fanclub by ID."""

    fanclub_repo: FantiaFanclubRepository

    def execute(self, fanclub_id: str) -> FantiaFanclub | None:
        """Execute the use case to get a fanclub by ID."""
        return self.fanclub_repo.get(fanclub_id)


@inject
@dataclass
class FantiaGetPostsUseCase:
    """Use case for getting posts by a Fantia fanclub ID."""

    post_repo: FantiaPostRepository

    def execute(self, post_ids: list[str]) -> list[FantiaPostData]:
        """Execute the use case to get posts by fanclub ID."""
        return self.post_repo.get_many(post_ids)
