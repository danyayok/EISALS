from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text, ARRAY, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    inn = Column(String(12), unique=True, index=True, nullable=False)
    kpp = Column(String(9), index=True, nullable=True)  # КПП 9 знаков, nullable для ИП

    company_name = Column(String(500), index=True)
    email = Column(String(255), unique=True, index=True)
    phone_number = Column(String(20))
    hashed_password = Column(String(255))
    region = Column(String(100))

    okpd2_codes = Column(ARRAY(String))
    okved_codes = Column(ARRAY(String))

    role = Column(String(20), default="supplier")  # supplier, analytic, admin
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Связи
    profile = relationship("CompanyProfile", back_populates="user", uselist=False)
    contracts = relationship("Contract", back_populates="supplier")
    posts = relationship("CompanyPost", back_populates="company")


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    full_name = Column(String(1000))
    short_name = Column(String(500))
    ogrn = Column(String(15), index=True)
    legal_address = Column(String(1000))
    actual_address = Column(String(1000))
    phone = Column(String(50))
    website = Column(String(500))

    # Агрегированная статистика (заполняется парсером)
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
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))

    title = Column(String(255))
    content = Column(Text)

    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("User", back_populates="posts")


class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    eis_id = Column(String, unique=True, index=True)
    registry_number = Column(String, index=True)

    title = Column(String(2000))
    description = Column(Text)

    # Данные заказчика
    customer_inn = Column(String(12), index=True)
    customer_kpp = Column(String(9), index=True)
    customer_name = Column(String(1000))

    okpd2_codes = Column(ARRAY(String))
    okved_codes = Column(ARRAY(String))
    region = Column(String)

    nmck = Column(Float)  # Начальная цена
    final_price = Column(Float)  # Цена контракта
    price_reduction = Column(Float)  # % снижения

    procedure_type = Column(String(255))
    participants_count = Column(Integer)

    # Данные победителя (могут быть пустыми до завершения)
    winner_inn = Column(String(12), index=True)
    winner_kpp = Column(String(9), index=True)
    winner_name = Column(String(1000))

    publication_date = Column(DateTime)
    submission_deadline = Column(DateTime)
    execution_period = Column(String(1000))

    status = Column(String)
    is_dumping = Column(Boolean, default=False)

    # Аналитические метрики
    market_price_adequacy = Column(String(50))
    risk_level = Column(String(50))
    win_probability = Column(Float)

    raw_data = Column(JSON)  # Храним исходный HTML или JSON ответа на всякий случай

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    eis_id = Column(String(100), unique=True, index=True)

    # Заказчик
    customer_inn = Column(String(12), index=True)
    customer_kpp = Column(String(9))
    customer_name = Column(String(1000))

    # Поставщик
    supplier_inn = Column(String(12), ForeignKey("users.inn"), index=True)
    supplier_kpp = Column(String(9))
    supplier_name = Column(String(1000))

    tender_id = Column(Integer, ForeignKey("tenders.id"))
    price = Column(Float)
    execution_date = Column(DateTime)
    termination_date = Column(DateTime, nullable=True)
    termination_reason = Column(Text, nullable=True)

    status = Column(String(100))
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
