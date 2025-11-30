"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


# User Schemas
class UserCreate(BaseModel):
    user_folder: str


class UserResponse(BaseModel):
    id: int
    user_folder: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Image Schemas
class ImageUpload(BaseModel):
    angle: str
    image_path: str


class ImageResponse(BaseModel):
    id: int
    user_id: int
    angle: str
    image_path: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Preference Schemas
class PreferenceCreate(BaseModel):
    gender: str
    size: str
    styles: List[str]
    clothing_types: List[str]
    budget: Optional[str] = None
    colors: Optional[str] = None
    notes: Optional[str] = None


class PreferenceResponse(BaseModel):
    id: int
    user_id: int
    gender: Optional[str]
    size: Optional[str]
    styles: Optional[List[str]]
    clothing_types: Optional[List[str]]
    budget: Optional[str]
    colors: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Product Schemas
class ProductCreate(BaseModel):
    product_id: str
    title: str
    price: Optional[str] = None
    extracted_price: Optional[float] = None
    old_price: Optional[str] = None
    product_link: str
    thumbnail: Optional[str] = None
    source: Optional[str] = None
    source_icon: Optional[str] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    snippet: Optional[str] = None
    delivery: Optional[str] = None
    tag: Optional[str] = None
    product_type: Optional[str] = None


class ProductResponse(BaseModel):
    id: int
    product_id: str
    title: str
    price: Optional[str]
    extracted_price: Optional[float]
    old_price: Optional[str]
    product_link: str
    thumbnail: Optional[str]
    source: Optional[str]
    rating: Optional[float]
    reviews: Optional[int]
    product_type: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Swipe Schemas
class SwipeCreate(BaseModel):
    product_id: int
    liked: bool


class SwipeResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    liked: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Product Click Schema
class ProductClickCreate(BaseModel):
    product_id: int
    referrer: Optional[str] = None


class ProductClickResponse(BaseModel):
    id: int
    user_id: Optional[int]
    product_id: int
    referrer: Optional[str]
    clicked_at: datetime
    
    class Config:
        from_attributes = True

