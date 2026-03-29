from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

INN_PATTERN = r"^(\d{10}|\d{12})$"
PHONE_PATTERN = r"^7\d{10}$"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    inn: Optional[str] = None


class UserBase(BaseModel):
    inn: str = Field(..., pattern=INN_PATTERN, description="ИНН организации или ИП")
    email: Optional[EmailStr] = None
    company_name: Optional[str] = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = Field(default=None, pattern=PHONE_PATTERN)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, value: str) -> str:
        has_lower = any(ch.islower() for ch in value)
        has_upper = any(ch.isupper() for ch in value)
        has_digit = any(ch.isdigit() for ch in value)
        has_special = any(not ch.isalnum() for ch in value)

        if not (has_lower and has_upper and has_digit and has_special):
            raise ValueError(
                "Пароль должен содержать строчные и заглавные буквы, цифры и спецсимволы"
            )

        return value


class UserLogin(BaseModel):
    inn: str = Field(..., pattern=INN_PATTERN)
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


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

    @field_validator("max_price")
    @classmethod
    def validate_price_range(cls, value, info):
        min_price = info.data.get("min_price")
        if value is not None and min_price is not None and value < min_price:
            raise ValueError("Максимальная цена не может быть меньше минимальной")
        return value
