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
import threading
import json

# Импорт Producer
from confluent_kafka import Producer

# Импорт модулей
from kafka import get_kafka_producer, kafka_consumer_service, redis_client
from data_models import UserMongo, UserDB, PlannedIncome, PlannedIncomeDB, PlannedExpenses, PlannedExpensesDB
from dependencies import get_db, get_current_client, SessionLocal
from settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, MONGO_URI, KAFKA_TOPIC

# Инициализация FastAPI
app = FastAPI()

# Подключение к MongoDB:
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["budgeting"]
mongo_users_collection = mongo_db["users"]

# Настройка паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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
@app.get("/users", response_model=List[UserMongo])
def search_users_by_name(
    first_name: str, last_name: str, current_user: str = Depends(get_current_client)
):
    users = list(mongo_users_collection.find({"first_name": {"$regex": first_name, "$options": "i"}, "last_name": {"$regex": last_name, "$options": "i"}}))
    for user in users:
        user["id"] = str(user["_id"])
    return users


# Создание планируемого дохода
@app.post("/incomes", response_model=PlannedIncome)
def create_planned_income(income: PlannedIncome, producer: Producer = Depends(get_kafka_producer), current_user: str = Depends(get_current_client)):
    producer.produce(KAFKA_TOPIC, key=str(income.user_id), value=json.dumps(income.dict()).encode("utf-8"))
    producer.flush()
    return income
    
# Запуск Kafka Consumer в фоновом режиме
def start_kafka_consumer():
    thread = threading.Thread(target=kafka_consumer_service, daemon=True)
    thread.start()

start_kafka_consumer()


# Перечень планируемых доходов
@app.get("/incomes", response_model=List[PlannedIncome])
def get_user_income(db: Session = Depends(get_db), current_user: str = Depends(get_current_client)):
    cache_key = 'incomes'
    cached_incomes = redis_client.get(cache_key)

    if cached_incomes:
        return [PlannedIncome(**income) for income in json.loads(cached_incomes)]

    incomes = db.query(PlannedIncomeDB).all()
    if incomes:
        redis_client.set(cache_key, json.dumps([income.dict() for income in incomes]))

    return incomes


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
# http://localhost:8000/openapi.json 
# http://localhost:8000/docs 


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)