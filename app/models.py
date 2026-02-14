from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text, ARRAY, JSON, column
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    inn = Column(String(12), unique=True, index=True, nullable=False)

    company_name = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    phone_number = Column(Integer(), unique=True, index=True)
    hashed_password = Column(String(255))
    region = Column(String(100))
    okpd2_codes = Column(ARRAY(String))
    okved_codes = Column(ARRAY(String))
    role = Column(String(20), default="supplier") # supplier, analytic (простой юзер), admin
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False) # админы будут заявки смотреть и принимать/отклонять
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    profile = relationship("CompanyProfile", back_populates="user")
    contracts = relationship("Contract", back_populates="supplier")
    posts = relationship("CompanyPost", back_populates="company")
    notifications = relationship("Notification", back_populates="user")

class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    full_name = Column(String(500))
    short_name = Column(String(255))
    legal_address = Column(String(500))
    actual_address = Column(String(500))
    phone = Column(String(25))
    website = Column(String(500))

    total_contracts = Column(Integer, default=0)
    completed_contracts = Column(Integer, default=0)
    terminated_contracts = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)

    avg_contract_price = Column(Float)
    max_contract_price = Column(Float)
    min_contract_price = Column(Float)

    achievements = Column(JSON, default=[])

    user = relationship("User", back_populates="profile")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class CompanyPost(Base):
    __tablename__ = "company_posts"
    id = Column(Integer, unique=True, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))

    title = Column(String(150))
    content = Column(String(1500))

    is_public = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("User", back_populates="posts")

class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    eis_id = Column(String(100), unique=True, index=True)
    registry_number = Column(String(100), index=True)

    title = Column(String(1000))
    description = Column(Text)
    customer_inn = Column(String(12), index=True)
    customer_name = Column(String(500))

    okpd2_codes = Column(ARRAY(String))
    okved_codes = Column(ARRAY(String))
    region = Column(String(100))

    nmck = Column(Float)
    final_price = Column(Float)
    price_reduction = Column(Float)

    procedure_type = Column(String(100))  # аукцион, конкурс, etc
    participants_count = Column(Integer)
    winner_inn = Column(String(12))
    winner_name = Column(String(500))

    publication_date = Column(DateTime)
    submission_deadline = Column(DateTime)
    execution_period = Column(String(500))

    status = Column(String(50))  # active, completed, canceled
    is_dumping = Column(Boolean, default=False)

    market_price_adequacy = Column(String(20))  # ниже_рынка, в_рынке, выше_рынка
    risk_level = Column(String(20))  # low, medium, high
    win_probability = Column(Float)  # Вероятность победы (0-1)

    raw_data = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    eis_id = Column(String(100), unique=True, index=True)

    customer_inn = Column(String(12), index=True)
    customer_name = Column(String(500))
    supplier_inn = Column(String(12), ForeignKey("users.inn"), index=True)
    supplier_name = Column(String(500))

    tender_id = Column(Integer, ForeignKey("tenders.id"))
    price = Column(Float)
    execution_date = Column(DateTime)
    termination_date = Column(DateTime, nullable=True)
    termination_reason = Column(String(500), nullable=True)

    status = Column(String(50))  # executing, completed, terminated
    delay_days = Column(Integer, default=0)

    supplier = relationship("User", back_populates="contracts")
    tender = relationship("Tender")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AnalyticsCache(Base):
    __tablename__ = "analytics_cache"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(500), unique=True, index=True)
    data = Column(JSON)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())