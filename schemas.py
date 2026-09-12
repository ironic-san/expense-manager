from datetime import date
from decimal import Decimal

from pydantic import (
    BaseModel,
    EmailStr,
    ConfigDict,
    Field
)


# ============================================================
# REGISTER
# ============================================================

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    salary: Decimal = Field(ge=0)


# ============================================================
# LOGIN
# ============================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ============================================================
# TOKEN RESPONSE
# ============================================================

class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# ============================================================
# USER RESPONSE
# ============================================================

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    name: str
    email: EmailStr
    salary: Decimal
    role: str


# ============================================================
# ADMIN USER RESPONSE
# ============================================================

class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    name: str
    email: EmailStr
    role: str


# ============================================================
# EXPENSE CREATE
# ============================================================

class ExpenseCreate(BaseModel):
    title: str
    amount: Decimal = Field(gt=0)
    category: str
    description: str | None = None
    expense_date: date


# ============================================================
# EXPENSE UPDATE
# ============================================================

class ExpenseUpdate(BaseModel):
    title: str
    amount: Decimal = Field(gt=0)
    category: str
    description: str | None = None
    expense_date: date


# ============================================================
# EXPENSE RESPONSE
# ============================================================

class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    expense_id: int
    user_id: int
    title: str
    amount: Decimal
    category: str
    description: str | None
    expense_date: date


# ============================================================
# AI ANALYSIS RESPONSE
# ============================================================

class AIAnalysisResponse(BaseModel):
    summary: str
    spending_patterns: list[str]
    related_expenses_summary: str
    risk_level: str
    assessment: str
    recommendation: str


# ============================================================
# EXPENSE CREATE RESPONSE
# ============================================================

class ExpenseCreateResponse(BaseModel):
    expense: ExpenseResponse
    ai_analysis: AIAnalysisResponse | None = None


# ============================================================
# UPDATE CURRENT USER PROFILE
# ============================================================

class UserUpdateRequest(BaseModel):
    name: str
    email: EmailStr
    salary: Decimal = Field(ge=0)


# ============================================================
# CHANGE CURRENT USER PASSWORD
# ============================================================

class PasswordUpdateRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)