from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from ..config.settings import settings

IS_SQLITE = settings.DATABASE_URL.startswith('sqlite')

if IS_SQLITE:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=1800,
        echo=settings.DEBUG
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class EnergyData(Base):
    __tablename__ = settings.ENERGY_TABLE_NAME
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    building_id = Column(String(50), index=True, nullable=False)
    building_type = Column(String(100))
    timestamp = Column(DateTime, index=True, nullable=False)
    electricity_kwh = Column(Float)
    water_m3 = Column(Float)
    hvac_kwh = Column(Float)
    chw_supply_temp = Column(Float)
    chw_return_temp = Column(Float)
    outdoor_temp = Column(Float)
    humidity_pct = Column(Float)
    occupancy_density = Column(Float)
    meter_id = Column(String(50))
    system_status = Column(String(20))


class Building(Base):
    __tablename__ = "buildings"
    
    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(String(50), unique=True, nullable=False)
    building_name = Column(String(200))
    building_type = Column(String(100))
    location = Column(String(200))
    total_area = Column(Float)
    floors = Column(Integer)
    year_built = Column(Integer)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Meter(Base):
    __tablename__ = "meters"
    
    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(String(50), unique=True, nullable=False)
    meter_name = Column(String(200))
    meter_type = Column(String(50))
    building_id = Column(String(50))
    location = Column(String(200))
    installation_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnomalyRecord(Base):
    __tablename__ = "anomaly_records"
    
    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(String(50), index=True)
    timestamp = Column(DateTime, index=True)
    anomaly_type = Column(String(50))
    severity = Column(String(20))
    description = Column(Text)
    metric_name = Column(String(100))
    metric_value = Column(Float)
    threshold = Column(Float)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500))
    category = Column(String(100))
    content = Column(Text)
    file_path = Column(String(500))
    file_type = Column(String(20))
    tags = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), unique=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200))
    role = Column(String(50), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
