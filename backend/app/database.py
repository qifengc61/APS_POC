from sqlalchemy import create_engine
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
                "ALTER TABLE products ADD COLUMN code VARCHAR(50) DEFAULT NULL AFTER name"
            )
            conn.commit()
    except Exception:
        pass
    try:
        with engine.connect() as conn:
            conn.execute("ALTER TABLE delivery_plans CHANGE COLUMN product_a_id product_1_id INT")
            conn.execute("ALTER TABLE delivery_plans CHANGE COLUMN product_b_id product_2_id INT")
            conn.execute("ALTER TABLE delivery_plans CHANGE COLUMN total_delivery_a total_delivery_1 FLOAT")
            conn.execute("ALTER TABLE delivery_plans CHANGE COLUMN total_delivery_b total_delivery_2 FLOAT")
            conn.execute("ALTER TABLE delivery_plans CHANGE COLUMN daily_deliveries_a daily_deliveries_1 TEXT")
            conn.execute("ALTER TABLE delivery_plans CHANGE COLUMN daily_deliveries_b daily_deliveries_2 TEXT")
            conn.commit()
    except Exception:
        pass
    try:
        with engine.connect() as conn:
            conn.execute("ALTER TABLE products DROP COLUMN initial_inventory")
            conn.commit()
    except Exception:
        pass
    try:
        with engine.connect() as conn:
            conn.execute("ALTER TABLE delivery_plans ADD COLUMN initial_inventory_1 FLOAT NOT NULL DEFAULT 0 AFTER product_2_id")
            conn.execute("ALTER TABLE delivery_plans ADD COLUMN initial_inventory_2 FLOAT NOT NULL DEFAULT 0 AFTER initial_inventory_1")
            conn.commit()
    except Exception:
        pass
