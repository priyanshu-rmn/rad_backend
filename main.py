import os
from typing import Annotated 
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import SQLModel, Session, create_engine, select
from loguru import logger as log

from auth import create_access_token, hash_password, verify_access_token, verify_password
from db_utils import check_db_connection
import models       

app = FastAPI()

#----------------------Database connection-----------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)


#using fastapi dependency
def get_session():
    with Session(engine) as db:
        yield db
        
SessionDep = Annotated[Session, Depends(get_session)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return payload  

UserDep = Annotated[dict, Depends(get_current_user)]
#----------------------ROUTES-----------------------------


@app.get("/")
async def home():
    return {"message": "Hello World"}

from pydantic import BaseModel
class Credentials(BaseModel):
    email: str
    password: str
    
# --------- AUTH -----------------
@app.post("/register/")
def register(user: Credentials, db: SessionDep):
    log.info("Registering ...", Credentials)
    db_user = db.exec(select(models.User).where(models.User.email == user.email)).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="email already registered",
        )
    hashed_password = hash_password(user.password)
    new_user = models.User(name="admin", email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

@app.post("/login/")
async def login(user:Credentials, db: SessionDep):
    log.info("Logging in ...", Credentials)
    db_user = db.exec(select(models.User).where(models.User.email == user.email)).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    access_token = create_access_token({"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}
  



@app.get("/protected/")
def protected_route(current_user: UserDep):
    log.info("Current user...", current_user)
    return {"message": f"Hello {current_user['sub']}, you are authenticated!"}

@app.get("/users/") 
async def read_users(
    db: SessionDep, 
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[models.User]:
    users = db.exec(select(models.User).offset(offset).limit(limit)).all()
    return users
    

#----------------------START_UP-----------------------------
@app.on_event("startup")
def on_startup():
    with Session(engine) as db:      
        connection_info = check_db_connection(db)
        log.info(connection_info)
        if connection_info["flag"]:
            log.success(connection_info["status"])
        else:
            log.info(connection_info["status"])
            log.error(connection_info["error"])
            exit()
    
    #create db and tables
    SQLModel.metadata.create_all(engine)
