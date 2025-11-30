"""
SQLAlchemy ORM models for StyleSwipe database.
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from backend.database import Base
except ImportError:
    from database import Base


class User(Base):
    """User accounts and metadata."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_folder = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    images = relationship("UserImage", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("Preference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    swipes = relationship("Swipe", back_populates="user", cascade="all, delete-orphan")
    liked_products = relationship("LikedProduct", back_populates="user", cascade="all, delete-orphan")
    product_clicks = relationship("ProductClick", back_populates="user", cascade="all, delete-orphan")


class UserImage(Base):
    """Paths to uploaded user images (front, side, back)."""
    __tablename__ = "user_images"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    angle = Column(String, nullable=False)  # 'front', 'side', 'back'
    image_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="images")


class Preference(Base):
    """User style preferences."""
    __tablename__ = "preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    gender = Column(String)
    size = Column(String)
    styles = Column(JSON)  # List of style strings
    clothing_types = Column(JSON)  # List of clothing type strings
    budget = Column(String)
    colors = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")


class Product(Base):
    """Searched/saved products from API."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, unique=True, index=True, nullable=False)  # From API
    title = Column(String, nullable=False)
    price = Column(String)
    extracted_price = Column(Float)
    old_price = Column(String)
    product_link = Column(Text, nullable=False)
    thumbnail = Column(Text)
    source = Column(String)
    source_icon = Column(Text)
    rating = Column(Float)
    reviews = Column(Integer)
    snippet = Column(Text)
    delivery = Column(String)
    tag = Column(String)
    product_type = Column(String, index=True)  # tops, bottoms, outerwear, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    swipes = relationship("Swipe", back_populates="product")
    liked_products = relationship("LikedProduct", back_populates="product")
    product_clicks = relationship("ProductClick", back_populates="product")


class Swipe(Base):
    """Swipe history (liked/disliked)."""
    __tablename__ = "swipes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    liked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="swipes")
    product = relationship("Product", back_populates="swipes")


class LikedProduct(Base):
    """Saved liked items with metadata."""
    __tablename__ = "liked_products"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    liked_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="liked_products")
    product = relationship("Product", back_populates="liked_products")


class ProductClick(Base):
    """Tracks each click to purchase link."""
    __tablename__ = "product_clicks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for anonymous clicks
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    referrer = Column(String)  # Where the click came from (e.g., 'results_page', 'swipe_page')
    clicked_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="product_clicks")
    product = relationship("Product", back_populates="product_clicks")

