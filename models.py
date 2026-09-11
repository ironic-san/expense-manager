from sqlalchemy import Column, BigInteger, Text, Numeric, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    password = Column(Text, nullable=False)
    salary = Column(Numeric(12, 2), nullable=False)
    role = Column(Text, nullable=False, default="user")

    expenses = relationship(
        "Expense",
        back_populates="user"
    )


class Expense(Base):
    __tablename__ = "expenses"

    expense_id = Column(BigInteger, primary_key=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.user_id"),
        nullable=False
    )
    title = Column(Text, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    category = Column(Text, nullable=False)
    description = Column(Text)
    expense_date = Column(Date, nullable=False)

    user = relationship(
        "User",
        back_populates="expenses"
    )