from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# Секретный ключ для подписи JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()


# Модель данных для пользователя
class User(BaseModel):
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


# Временное хранилище для пользователей, доходов и расходов
users_db = []
planned_incomes_db = []
planned_expenses_db = []


# Псевдо-база данных пользователей
client_db = {
    "admin":  "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # hashed "secret"
}


# Настройка паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Настройка OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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
    password_check = False
    if form_data.username in client_db:
        password = client_db[form_data.username]
        if pwd_context.verify(form_data.password, password):
            password_check = True


    if password_check:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": form_data.username}, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    

# Создание нового пользователя
@app.post("/users", response_model=User)
def create_user(user: User, current_user: str = Depends(get_current_client)):
    for u in users_db:
        if u.id == user.id:
            raise HTTPException(status_code=404, detail="User already exists")
    users_db.append(user)
    return user


# Поиск пользователя по логину
@app.get("/users/{username}", response_model=User)
def get_user_by_username(username: str, current_user: str = Depends(get_current_client)):
    for user in users_db:
        if user.username == username:
            return user
    raise HTTPException(status_code=404, detail="User not found")


# Поиск пользователя по маске имени и фамилии
@app.get("/users", response_model=List[User])
def search_users_by_name(
    first_name: str, last_name: str, current_user: str = Depends(get_current_client)
):
    matching_users = [
        user
        for user in users_db
        if first_name.lower() in user.first_name.lower()
        and last_name.lower() in user.last_name.lower()
    ]
    return matching_users


# Создание планируемого дохода
@app.post("/incomes/", response_model=PlannedIncome)
def create_planned_income(income: PlannedIncome):
    planned_incomes_db.append(income)
    return income


# Перечень планируемых доходов
@app.get("/incomes/", response_model=List[PlannedIncome])
def get_planned_incomes():
    return planned_incomes_db


# Создание планируемого расхода
@app.post("/expenses/", response_model=PlannedExpenses)
def create_planned_expense(expense: PlannedExpenses):
    planned_expenses_db.append(expense)
    return expense


# Перечень планируемых расходов
@app.get("/expenses/", response_model=List[PlannedExpenses])
def get_planned_expenses():
    return planned_expenses_db


# Подсчёт динамики бюджета за период
@app.get("/budget_dynamics/")
def get_budget_dynamics(start_date: datetime, end_date: datetime):
    incomes = [income.amount for income in planned_incomes_db if start_date <= income.date <= end_date]
    expenses = [expense.amount for expense in planned_expenses_db if start_date <= expense.date <= end_date]
    total_income = sum(incomes)
    total_expense = sum(expenses)
    balance = total_income - total_expense
    return {"total_income": total_income, "total_expense": total_expense, "balance": balance}



# Запуск сервера
# http://localhost:8000/openapi.json swagger
# http://localhost:8000/docs портал документации


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
