from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, ARRAY, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pymongo import MongoClient
from bson import ObjectId


# Настройка PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:archdb@db/budgeting"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Секретный ключ для подписи JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()


# Настройка паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Настройка OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Подключение к MongoDB:
MONGO_URI = "mongodb://root:pass@mongo:27017/"
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["budgeting"]
mongo_users_collection = mongo_db["users"]


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
    




# Зависимости для получения текущего пользователя
async def get_current_client(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        else:
            return username
    except JWTError:
        raise credentials_exception


# Создание и проверка JWT токенов
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Маршрут для получения токена
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.username == form_data.username).first()
    db.close()

    if user and pwd_context.verify(form_data.password, user.hashed_password):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    

# Создание нового пользователя
@app.post("/users", response_model=UserMongo)
def create_user(user: UserMongo, current_user: str = Depends(get_current_client)):
    user_dict = user.dict()
    user_dict["hashed_password"] = pwd_context.hash(user_dict["hashed_password"])
    user_id = mongo_users_collection.insert_one(user_dict).inserted_id
    user_dict["id"] = str(user_id)
    return user_dict


# Поиск пользователя по логину
@app.get("/users/{username}", response_model=UserMongo)
def get_user_by_username(username: str, current_user: str = Depends(get_current_client)):
    user = mongo_users_collection.find_one({"username": username})
    if user:
        user["id"] = str(user["_id"])
        return user
    raise HTTPException(status_code=404, detail="User not found")


# Поиск пользователя по маске имени и фамилии
@app.get("/users", response_model=List[User])
def search_users_by_name(
    first_name: str, last_name: str, current_user: str = Depends(get_current_client)
):
    users = list(mongo_users_collection.find({"first_name": {"$regex": first_name, "$options": "i"}, "last_name": {"$regex": last_name, "$options": "i"}}))
    for user in users:
        user["id"] = str(user["_id"])
    return users


# Создание планируемого дохода
@app.post("/incomes", response_model=PlannedIncome)
def create_planned_income(income: PlannedIncome, current_user: str = Depends(get_current_client)):
    db = SessionLocal()
    db_income = PlannedIncomeDB(**income.dict())
    db.add(db_income)
    db.commit()
    db.refresh(db_income)
    db.close()
    return income


# Перечень планируемых доходов
@app.get("/incomes", response_model=List[PlannedIncome])
def get_user_income(user_id: int, current_user: str = Depends(get_current_client)):
    db = SessionLocal()
    try:
        income = db.query(PlannedIncomeDB).filter(PlannedIncomeDB.user_id == user_id).all()
        if not income:
            raise HTTPException(status_code=404, detail="Income not found")
        return income
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# Создание планируемого расхода
@app.post("/expenses", response_model=PlannedExpenses)
def create_planned_expense(expense: PlannedExpenses, current_user: str = Depends(get_current_client)):
    db = SessionLocal()
    db_expense = PlannedExpensesDB(**expense.dict())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    db.close()
    return expense


# Перечень планируемых расходов
@app.get("/expenses", response_model=List[PlannedExpenses])
def get_user_expense(user_id: int, current_user: str = Depends(get_current_client)):
    db = SessionLocal()
    try:
        expense = db.query(PlannedExpensesDB).filter(PlannedExpensesDB.user_id == user_id).all()
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        return expense
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# Подсчёт динамики бюджета за период
@app.get("/budget_dynamics/")
def get_budget_dynamics(start_date: datetime, end_date: datetime, current_user: str = Depends(get_current_client)):
    db = SessionLocal()
    try:
        incomes = db.query(PlannedIncomeDB).filter(PlannedIncomeDB.date.between(start_date, end_date)).all()
        expenses = db.query(PlannedExpensesDB).filter(PlannedExpensesDB.date.between(start_date, end_date)).all()
        total_income = sum(income.amount for income in incomes)
        total_expense = sum(expense.amount for expense in expenses)
        balance = total_income - total_expense
        return {"total_income": total_income, "total_expense": total_expense, "balance": balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()




# Запуск сервера
# http://localhost:8000/openapi.json swagger
# http://localhost:8000/docs портал документации


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)