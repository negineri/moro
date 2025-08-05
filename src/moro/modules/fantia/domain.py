"""Domain model for Fantia client."""

from typing import Annotated, Any, Protocol

from pydantic import BaseModel, Field


class SessionIdProvider(Protocol):
    """Abstract base class for providing Fantia session IDs."""

    def get_cookies(self) -> dict[str, str]:
        """Get all Fantia-related cookies.

        Returns:
            Dictionary containing cookies. May include:
            - _session_id: Main session identifier
            - jp_chatplus_vtoken: Chat plus token
            - _f_v_k_1: Fantia verification key
        """
        ...


# Value objects for Fantia post data


class FantiaURL(BaseModel):
    """Data model for Fantia post file."""

    url: Annotated[str, Field(description="The URL to download the file")]
    ext: Annotated[str, Field(description="The file extension")]


class FantiaPhotoGallery(BaseModel):
    """Data model for Fantia post photo gallery."""

    id: Annotated[str, Field(description="The ID of the photo")]
    title: Annotated[str, Field(description="The title of the photo")]
    comment: Annotated[str | None, Field(description="The comment of the photo")]
    photos: Annotated[list[FantiaURL], Field(description="The URLs of the photos in the gallery")]


class FantiaFile(BaseModel):
    """Data model for Fantia post file."""

    id: Annotated[str, Field(description="The ID of the file")]
    title: Annotated[str, Field(description="The title of the file")]
    comment: Annotated[str | None, Field(description="The comment of the file")]
    url: Annotated[str, Field(description="The URL to download the file")]
    name: Annotated[str, Field(description="The name of the file")]


class FantiaText(BaseModel):
    """Data model for Fantia post text content."""

    id: Annotated[str, Field(description="The ID of the text content")]
    title: Annotated[str, Field(description="The title of the text content")]
    comment: Annotated[str | None, Field(description="The comment of the text content")]


class FantiaProduct(BaseModel):
    """Data model for Fantia product."""

    id: Annotated[str, Field(description="The ID of the product")]
    title: Annotated[str, Field(description="The title of the product")]
    comment: Annotated[str | None, Field(description="The comment of the product")]
    name: Annotated[str, Field(description="The name of the product")]
    url: Annotated[str, Field(description="The URL of the product")]


class FantiaPostData(BaseModel):
    """Data model for Fantia post data."""

    id: Annotated[str, Field(description="The ID of the post")]
    title: Annotated[str, Field(description="The title of the post")]
    creator_name: Annotated[str, Field(description="The name of the post creator")]
    creator_id: Annotated[str, Field(description="The ID of the post creator")]
    contents: Annotated[list[Any], Field(description="The contents of the post")]
    contents_photo_gallery: Annotated[
        list[FantiaPhotoGallery], Field(description="The photo gallery of the post")
    ]
    contents_files: Annotated[list[FantiaFile], Field(description="The files of the post")]
    contents_text: Annotated[list[FantiaText], Field(description="The text contents of the post")]
    contents_products: Annotated[list[FantiaProduct], Field(description="The products of the post")]
    posted_at: Annotated[int, Field(description="The timestamp when the post was created")]
    converted_at: Annotated[int, Field(description="The timestamp when the post was converted")]
    comment: Annotated[str | None, Field(description="The comment of the post")]
    thumbnail: Annotated[FantiaURL | None, Field(description="The URL of the post thumbnail")]


# ===== Repository Interfaces =====


class FantiaFanclub(BaseModel):
    """Data model for Fantia fanclub."""

    id: Annotated[str, Field(description="The ID of the fanclub")]
    posts: Annotated[list[str], Field(description="List of post IDs by this fanclub")]


class FantiaPostRepository(Protocol):
    """Repository interface for Fantia post data access."""

    def get(self, post_id: str) -> FantiaPostData | None:
        """Get a single post by ID.

        Args:
            post_id: The ID of the post to retrieve

        Returns:
            FantiaPostData if found, None otherwise
        """
        ...

    def get_many(self, post_ids: list[str]) -> list[FantiaPostData]:
        """Get multiple posts by IDs.

        Args:
            post_ids: List of post IDs to retrieve

        Returns:
            List of FantiaPostData for found posts (excludes not found)
        """
        ...


class FantiaFanclubRepository(Protocol):
    """Repository interface for Fantia fanclub data access."""

    def get(self, fanclub_id: str) -> FantiaFanclub | None:
        """Get a fanclub by ID.

        Args:
            fanclub_id: The ID of the fanclub to retrieve

        Returns:
            FantiaFanclub if found, None otherwise
        """
        ...
