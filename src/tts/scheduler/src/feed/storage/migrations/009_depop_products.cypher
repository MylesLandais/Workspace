// Depop product and price tracking schema
// Run this migration to set up the graph database for e-commerce products

// Create constraints for unique properties
CREATE CONSTRAINT product_id_unique IF NOT EXISTS
FOR (p:Product) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT seller_username_unique IF NOT EXISTS
FOR (s:Seller) REQUIRE s.username IS UNIQUE;

CREATE CONSTRAINT price_history_id_unique IF NOT EXISTS
FOR (ph:PriceHistory) REQUIRE ph.id IS UNIQUE;

// Create indexes for common queries
CREATE INDEX product_created_utc_index IF NOT EXISTS
FOR (p:Product) ON (p.created_utc);

CREATE INDEX product_price_index IF NOT EXISTS
FOR (p:Product) ON (p.price);

CREATE INDEX product_status_index IF NOT EXISTS
FOR (p:Product) ON (p.status);

CREATE INDEX product_brand_index IF NOT EXISTS
FOR (p:Product) ON (p.brand);

CREATE INDEX product_category_index IF NOT EXISTS
FOR (p:Product) ON (p.category);

CREATE INDEX price_history_timestamp_index IF NOT EXISTS
FOR (ph:PriceHistory) ON (ph.timestamp);

CREATE INDEX price_history_price_index IF NOT EXISTS
FOR (ph:PriceHistory) ON (ph.price);

// Create full-text index for product search
CREATE FULLTEXT INDEX product_search_index IF NOT EXISTS
FOR (p:Product) ON EACH [p.title, p.description];







