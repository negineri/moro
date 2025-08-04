"""Usecases for Fantia module."""

from dataclasses import dataclass
from typing import Optional

from injector import inject

from moro.modules.fantia.domain import (
    FantiaFanclub,
    FantiaFanclubRepository,
)


@inject
@dataclass
class FantiaGetFanclubUseCase:
    """Use case for getting a Fantia fanclub by ID."""

    fanclub_repo: FantiaFanclubRepository

    def execute(self, fanclub_id: str) -> Optional[FantiaFanclub]:
        """Execute the use case to get a fanclub by ID."""
        return self.fanclub_repo.get(fanclub_id)
