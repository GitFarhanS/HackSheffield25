# PostgreSQL Database Setup

## Quick Start with Docker

1. Start PostgreSQL:
```bash
docker-compose up -d
```

2. Add to `.env`:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/styleswipe
```

3. Run the backend - tables will be created automatically on startup.

## Manual PostgreSQL Setup

1. Install PostgreSQL locally
2. Create database:
```sql
CREATE DATABASE styleswipe;
```

3. Add to `.env`:
```
DATABASE_URL=postgresql://username:password@localhost:5432/styleswipe
```

## Database Schema

The following tables are created automatically:

- `users` - User accounts
- `user_images` - Uploaded image paths
- `preferences` - User style preferences
- `products` - Products from search API
- `swipes` - Swipe history (liked/disliked)
- `liked_products` - Saved liked items
- `product_clicks` - Click tracking for analytics

## Grafana Integration

1. Add PostgreSQL data source in Grafana
2. Connection string: `postgresql://postgres:postgres@localhost:5432/styleswipe`
3. Create dashboards using SQL queries on the tables

### Example Queries

**Click-through rate:**
```sql
SELECT 
  p.title,
  COUNT(DISTINCT lp.id) as likes,
  COUNT(DISTINCT pc.id) as clicks,
  CASE 
    WHEN COUNT(DISTINCT lp.id) > 0 
    THEN ROUND(100.0 * COUNT(DISTINCT pc.id) / COUNT(DISTINCT lp.id), 2)
    ELSE 0 
  END as ctr_percent
FROM products p
LEFT JOIN liked_products lp ON p.id = lp.product_id
LEFT JOIN product_clicks pc ON p.id = pc.product_id
GROUP BY p.id, p.title
ORDER BY clicks DESC;
```

**Popular product types:**
```sql
SELECT 
  product_type,
  COUNT(*) as product_count,
  COUNT(DISTINCT lp.user_id) as unique_likers
FROM products p
LEFT JOIN liked_products lp ON p.id = lp.product_id
WHERE product_type IS NOT NULL
GROUP BY product_type
ORDER BY product_count DESC;
```

