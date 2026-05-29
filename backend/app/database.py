from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "mysql+pymysql://root:scheduling123@127.0.0.1:3307/smart_scheduling?charset=utf8mb4"

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    try:
        with engine.connect() as conn:
            conn.execute(
                text("ALTER TABLE products ADD COLUMN code VARCHAR(50) DEFAULT NULL AFTER name")
            )
            conn.commit()
    except Exception:
        pass
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE products DROP COLUMN initial_inventory"))
            conn.commit()
    except Exception:
        pass
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS plan_materials (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    plan_id INT NOT NULL,
                    line_product_id INT NOT NULL,
                    initial_inventory FLOAT NOT NULL DEFAULT 0,
                    total_delivery FLOAT NOT NULL DEFAULT 0,
                    daily_deliveries TEXT DEFAULT NULL,
                    sort_order INT NOT NULL DEFAULT 0,
                    FOREIGN KEY (plan_id) REFERENCES delivery_plans(id) ON DELETE CASCADE,
                    FOREIGN KEY (line_product_id) REFERENCES line_products(id) ON DELETE CASCADE
                )
            """))
            conn.commit()
    except Exception:
        pass
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM plan_materials"))
            count = result.scalar()
            if count == 0:
                try:
                    conn.execute(text("""
                        INSERT INTO plan_materials (plan_id, line_product_id, initial_inventory, total_delivery, daily_deliveries, sort_order)
                        SELECT id, product_1_id, initial_inventory_1, total_delivery_1, daily_deliveries_1, 0
                        FROM delivery_plans
                        WHERE product_1_id IS NOT NULL
                    """))
                except Exception:
                    pass
                try:
                    conn.execute(text("""
                        INSERT INTO plan_materials (plan_id, line_product_id, initial_inventory, total_delivery, daily_deliveries, sort_order)
                        SELECT id, product_2_id, initial_inventory_2, total_delivery_2, daily_deliveries_2, 1
                        FROM delivery_plans
                        WHERE product_2_id IS NOT NULL
                    """))
                except Exception:
                    pass
                conn.commit()
    except Exception:
        pass
    try:
        with engine.connect() as conn:
            for fk in ["delivery_plans_ibfk_2", "delivery_plans_ibfk_3"]:
                try:
                    conn.execute(text(f"ALTER TABLE delivery_plans DROP FOREIGN KEY {fk}"))
                except Exception:
                    pass
            for col in ["product_1_id", "product_2_id", "initial_inventory_1", "initial_inventory_2", "total_delivery_1", "total_delivery_2", "daily_deliveries_1", "daily_deliveries_2"]:
                try:
                    conn.execute(text(f"ALTER TABLE delivery_plans DROP COLUMN {col}"))
                except Exception:
                    pass
            conn.commit()
    except Exception:
        pass
