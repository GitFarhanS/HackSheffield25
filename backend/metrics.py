"""
Prometheus metrics for StyleSwipe application.
Exposes custom application metrics for Grafana dashboards.
"""

from prometheus_client import (
    Counter, Gauge, Histogram, 
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, REGISTRY
)
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func

try:
    from backend.models import User, Preference, Product, Swipe, LikedProduct, ProductClick
    from backend.database import SessionLocal
except ImportError:
    from models import User, Preference, Product, Swipe, LikedProduct, ProductClick
    from database import SessionLocal


# ==================== GAUGES (current state) ====================

# User demographics
styleswipe_users_total = Gauge(
    'styleswipe_users_total',
    'Total number of users'
)

styleswipe_users_by_gender = Gauge(
    'styleswipe_users_by_gender',
    'Number of users by gender',
    ['gender']
)

styleswipe_users_by_size = Gauge(
    'styleswipe_users_by_size',
    'Number of users by clothing size',
    ['size']
)

# Product metrics
styleswipe_products_total = Gauge(
    'styleswipe_products_total',
    'Total number of products in database'
)

styleswipe_products_by_type = Gauge(
    'styleswipe_products_by_type',
    'Number of products by clothing type',
    ['clothing_type']
)

# Swipe metrics
styleswipe_swipes_total = Gauge(
    'styleswipe_swipes_total',
    'Total number of swipes',
    ['action']  # 'liked' or 'disliked'
)

styleswipe_likes_total = Gauge(
    'styleswipe_likes_total',
    'Total number of liked products'
)

styleswipe_dislikes_total = Gauge(
    'styleswipe_dislikes_total',
    'Total number of disliked products'
)

# Click metrics
styleswipe_clicks_total = Gauge(
    'styleswipe_clicks_total',
    'Total number of product link clicks'
)

styleswipe_clicks_by_product_type = Gauge(
    'styleswipe_clicks_by_product_type',
    'Clicks by product clothing type',
    ['clothing_type']
)

# Click-through rate metrics
styleswipe_ctr_by_product_type = Gauge(
    'styleswipe_ctr_by_product_type',
    'Click-through rate (clicks/likes) by product type',
    ['clothing_type']
)

# Style popularity
styleswipe_style_popularity = Gauge(
    'styleswipe_style_popularity',
    'Popularity of different styles',
    ['style']
)

# ==================== COUNTERS (cumulative) ====================

styleswipe_api_requests = Counter(
    'styleswipe_api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status']
)


def collect_metrics():
    """
    Collect all metrics from database and update Prometheus gauges.
    Called on each /metrics request for fresh data.
    """
    db = SessionLocal()
    try:
        # === User metrics ===
        total_users = db.query(User).count()
        styleswipe_users_total.set(total_users)
        
        # Users by gender
        gender_counts = db.query(
            Preference.gender,
            sql_func.count(Preference.id)
        ).group_by(Preference.gender).all()
        
        # Reset all gender labels first
        for gender in ['male', 'female', 'non-binary', 'other', None]:
            label = gender if gender else 'unknown'
            styleswipe_users_by_gender.labels(gender=label).set(0)
        
        for gender, count in gender_counts:
            label = gender if gender else 'unknown'
            styleswipe_users_by_gender.labels(gender=label).set(count)
        
        # Users by size
        size_counts = db.query(
            Preference.size,
            sql_func.count(Preference.id)
        ).group_by(Preference.size).all()
        
        for size, count in size_counts:
            label = size if size else 'unknown'
            styleswipe_users_by_size.labels(size=label).set(count)
        
        # === Product metrics ===
        total_products = db.query(Product).count()
        styleswipe_products_total.set(total_products)
        
        # Products by type
        type_counts = db.query(
            Product.product_type,
            sql_func.count(Product.id)
        ).group_by(Product.product_type).all()
        
        for product_type, count in type_counts:
            label = product_type if product_type else 'unknown'
            styleswipe_products_by_type.labels(clothing_type=label).set(count)
        
        # === Swipe metrics ===
        likes_count = db.query(Swipe).filter(Swipe.liked == True).count()
        dislikes_count = db.query(Swipe).filter(Swipe.liked == False).count()
        
        styleswipe_swipes_total.labels(action='liked').set(likes_count)
        styleswipe_swipes_total.labels(action='disliked').set(dislikes_count)
        styleswipe_likes_total.set(likes_count)
        styleswipe_dislikes_total.set(dislikes_count)
        
        # === Click metrics ===
        total_clicks = db.query(ProductClick).count()
        styleswipe_clicks_total.set(total_clicks)
        
        # Clicks by product type
        click_by_type = db.query(
            Product.product_type,
            sql_func.count(ProductClick.id)
        ).join(ProductClick, Product.id == ProductClick.product_id
        ).group_by(Product.product_type).all()
        
        for product_type, count in click_by_type:
            label = product_type if product_type else 'unknown'
            styleswipe_clicks_by_product_type.labels(clothing_type=label).set(count)
        
        # === Click-through rate by product type ===
        # CTR = clicks / likes for each product type
        likes_by_type = db.query(
            Product.product_type,
            sql_func.count(LikedProduct.id)
        ).join(LikedProduct, Product.id == LikedProduct.product_id
        ).group_by(Product.product_type).all()
        
        likes_dict = {ptype: count for ptype, count in likes_by_type}
        clicks_dict = {ptype: count for ptype, count in click_by_type}
        
        all_types = set(likes_dict.keys()) | set(clicks_dict.keys())
        for product_type in all_types:
            likes = likes_dict.get(product_type, 0)
            clicks = clicks_dict.get(product_type, 0)
            ctr = (clicks / likes * 100) if likes > 0 else 0
            label = product_type if product_type else 'unknown'
            styleswipe_ctr_by_product_type.labels(clothing_type=label).set(ctr)
        
        # === Style popularity ===
        # Count how many users selected each style
        all_prefs = db.query(Preference.styles).all()
        style_counts = {}
        for (styles,) in all_prefs:
            if styles:
                for style in styles:
                    style_counts[style] = style_counts.get(style, 0) + 1
        
        for style, count in style_counts.items():
            styleswipe_style_popularity.labels(style=style).set(count)
        
    finally:
        db.close()


def get_metrics():
    """Generate Prometheus metrics output."""
    collect_metrics()
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST

