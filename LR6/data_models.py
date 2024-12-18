from pydantic import BaseModel
from typing import List
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Optional, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Модель данных для пользователя
class UserMongo(BaseModel):
    id: int
    username: str
    first_name : str
    last_name : str
    email: str
    hashed_password: str
    age: Optional[int] = None


# Модель данных для планируемых доходов
class PlannedIncome(BaseModel):
    id : int
    user_id : int
    amount : float
    description : str
    date : datetime
    

# Модель данных для планируемых расходов
class PlannedExpenses(BaseModel):
    id : int
    user_id : int
    amount : float
    description : str
    date : datetime
    



    # SQLAlchemy models
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True)
    age = Column(Integer)


class PlannedIncomeDB(Base):
    __tablename__ = "income"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    description = Column(String)
    date = Column(DateTime)
    

class PlannedExpensesDB(Base):
    __tablename__ = "expense"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    description = Column(String)
    date = Column(DateTime)
    