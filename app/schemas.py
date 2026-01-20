from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal # Добавили для точности денег

# Базовые схемы
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    inn: Optional[str] = None

# Пользовательские схемы
class UserBase(BaseModel):
    inn: str = Field(..., pattern=r'^(\d{10}|\d{12})$', description="ИНН организации или ИП")
    email: Optional[EmailStr] = None
    company_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    inn: str = Field(..., pattern=r'^(\d{10}|\d{12})$')
    password: str

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Схемы для профиля
class CompanyProfileBase(BaseModel):
    full_name: Optional[str] = None
    region: Optional[str] = None
    okpd2_codes: Optional[List[str]] = None

class CompanyProfileResponse(CompanyProfileBase):
    total_contracts: int
    completed_contracts: int
    completion_rate: float
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Схемы для закупок
class TenderBase(BaseModel):
    eis_id: str
    title: str
    customer_name: str
    nmck: Decimal = Field(..., max_digits=15, decimal_places=2)
    region: str

class TenderResponse(TenderBase):
    id: int
    price_reduction: Optional[float] = None
    participants_count: Optional[int] = None
    status: str
    market_price_adequacy: Optional[str] = None
    risk_level: Optional[str] = None
    win_probability: Optional[float] = None
    publication_date: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class TenderFilters(BaseModel):
    okpd2_codes: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = None
    procedure_types: Optional[List[str]] = None
    status: Optional[str] = "active"

    @field_validator('max_price')
    @classmethod
    def validate_price_range(cls, v, info):
        min_p = info.data.get('min_price')
        if v is not None and min_p is not None and v < min_p:
            raise ValueError('Максимальная цена не может быть меньше минимальной')
        return v
