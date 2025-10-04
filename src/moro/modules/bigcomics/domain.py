"""BigComics domain models."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class Cookie(BaseModel):
    """Cookie model for playwright."""

    name: str
    value: str
    domain: str
    path: str
    expires: float
    http_only: Annotated[bool, Field(..., alias="httpOnly")]
    secure: bool
    same_site: Annotated[Literal["Lax", "None", "Strict"], Field(..., alias="sameSite")]
    partition_key: Annotated[str | None, Field(..., alias="partitionKey")] = None
