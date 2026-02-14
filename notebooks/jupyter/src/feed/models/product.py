"""Product model for e-commerce products."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Product(BaseModel):
    """Represents an e-commerce product listing."""

    id: str = Field(..., description="Unique product identifier")
    title: str = Field(..., description="Product title")
    description: str = Field(default="", description="Product description")
    price: float = Field(..., description="Current price")
    currency: str = Field(default="USD", description="Currency code (USD, GBP, EUR, etc.)")
    status: str = Field(default="ONSALE", description="Product status (ONSALE, SOLD, etc.)")
    brand: Optional[str] = Field(default=None, description="Product brand")
    condition: Optional[str] = Field(default=None, description="Item condition (new, used, etc.)")
    size: Optional[str] = Field(default=None, description="Product size")
    category: Optional[str] = Field(default=None, description="Product category")
    tags: List[str] = Field(default_factory=list, description="Product tags/hashtags")
    image_urls: List[str] = Field(default_factory=list, description="List of product image URLs")
    seller_username: Optional[str] = Field(default=None, description="Seller username")
    seller_id: Optional[str] = Field(default=None, description="Seller ID")
    likes_count: int = Field(default=0, description="Number of likes")
    created_utc: datetime = Field(..., description="Listing creation timestamp (UTC)")
    updated_utc: Optional[datetime] = Field(default=None, description="Last update timestamp (UTC)")
    url: str = Field(..., description="Product URL")
    permalink: Optional[str] = Field(default=None, description="Product permalink/slug")

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }







