from datetime import datetime
import os
from typing import Annotated, Optional 
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import SQLModel, Session, create_engine, select, func
from loguru import logger as log

from auth import create_access_token, hash_password, verify_access_token, verify_password
from db_utils import check_db_connection
from models import Application, ApplicationStatusEnum, PositionStatusEnum, User, Position     

app = FastAPI()
#---------------------------CORS setup-------------------
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#----------------------Database connection-----------------------------
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(".env"))
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


# --------- AUTH -----------------
from pydantic import BaseModel
class Credentials(BaseModel):
    email: str
    password: str
    
@app.post("/register/")
def register(user: Credentials, db: SessionDep):
    log.info("Registering ...", Credentials)
    db_user = db.exec(select(User).where(User.email == user.email)).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="email already registered",
        )
    hashed_password = hash_password(user.password)
    new_user = User(name="admin", email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

@app.post("/login/")
async def login(user:Credentials, db: SessionDep):
    log.info("Logging in ...", Credentials)
    db_user = db.exec(select(User).where(User.email == user.email)).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    access_token = create_access_token({"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}
  



#----------------------ROUTES-----------------------------
@app.get("/")
async def home():
    return {"message": "Hello World"}

@app.get("/protected/")
def protected_route(current_user: UserDep):
    log.info("Current user...", current_user)
    return {"message": f"Hello {current_user['sub']}, you are authenticated!"}


@app.get("/time_to_fill/")
async def time_to_fill(
    db: SessionDep,
    current_user: UserDep,
    start_date: Optional[datetime] = Query(None, description="Filter positions created after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter positions created before this date"),
):
    log.info(current_user);
    
    # Build the base query
    query = select(Position).where(Position.status == PositionStatusEnum.FILLED)

    # Apply start_date filter if provided
    if start_date:
        query = query.where(Position.created_at >= start_date)

    # Apply end_date filter if provided
    if end_date:
        query = query.where(Position.created_at <= end_date)

    # Execute the query and fetch results
    results = db.exec(query).all()

    return results



@app.get("/time_to_hire/")
async def time_to_hire(
    db: SessionDep,
    current_user: UserDep,
    
):
    pass


@app.get("/candidate_pipeline/")
async def candidate_pipeline_metric(
    db: SessionDep,
    # current_user: UserDep,
    application_status: Optional[list[str]] = Query(None, description="Filter by application status"),
    positions: Optional[list[int]] = Query(None, description="Filter by position IDs"),
    applied_at_start: Optional[datetime] = Query(None, description="Filter applications applied after this date"),
    applied_at_end: Optional[datetime] = Query(None, description="Filter applications applied before this date"),
    last_updated_start: Optional[datetime] = Query(None, description="Filter applications updated after this date"),
    last_updated_end: Optional[datetime] = Query(None, description="Filter applications updated before this date"),
):
    print(application_status)
    # Build the base query
    query = (
        select(
            Application.last_stage_name,
            func.count().label("count")
        )
        .group_by(Application.last_stage_name)
    )
    # Apply filters based on query parameters
    if application_status:
        query = query.where(Application.status.in_(application_status))
    if positions:
        query = query.where(Application.position_id.in_(positions))
    if applied_at_start:
        query = query.where(Application.applied_at >= applied_at_start)
    if applied_at_end:
        query = query.where(Application.applied_at <= applied_at_end)
    if last_updated_start:
        query = query.where(Application.last_updated >= last_updated_start)
    if last_updated_end:
        query = query.where(Application.last_updated <= last_updated_end)

    # Execute the query
    log.critical(query)
    results = db.exec(query)
    
    response = [{"last_stage_name": row[0] if row[0] else "YET_TO_START", "count": row[1]} for row in results]

    return response
    

@app.get("/offer_details/")
async def offer_details(
    db: SessionDep,
    # current_user: UserDep,
    positions: Optional[list[int]] = Query(None, description="Filter by position IDs"),
    applied_at_start: Optional[datetime] = Query(None, description="Filter applications applied after this date"),
    applied_at_end: Optional[datetime] = Query(None, description="Filter applications applied before this date"),
    last_updated_start: Optional[datetime] = Query(None, description="Filter applications updated after this date"),
    last_updated_end: Optional[datetime] = Query(None, description="Filter applications updated before this date"),
):
    # Build the base query
    query = (
        select(
            Application.status,
            func.count().label("count")
        )
        .where(Application.status.in_([ApplicationStatusEnum.OFFERED, ApplicationStatusEnum.ACCEPTED, ApplicationStatusEnum.DECLINED]))
        .group_by(Application.status)
    )
    # Apply filters based on query parameters
    
    if positions:
        query = query.where(Application.position_id.in_(positions))
    if applied_at_start:
        query = query.where(Application.applied_at >= applied_at_start)
    if applied_at_end:
        query = query.where(Application.applied_at <= applied_at_end)
    if last_updated_start:
        query = query.where(Application.last_updated >= last_updated_start)
    if last_updated_end:
        query = query.where(Application.last_updated <= last_updated_end)

    # Execute the query
    log.critical(query)
    results = db.exec(query)
    response = [{"status": row[0] , "count": row[1]} for row in results]

    return response
    

@app.get("/candidate_waiting_noaction_new/")
async def candidates_waiting(  
    db: SessionDep,                             
    # current_user: UserDep,
    positions: Optional[list[int]] = Query(None, description="Filter by position IDs"),
    applied_at_start: Optional[datetime] = Query(None, description="Filter applications applied after this date"),
    applied_at_end: Optional[datetime] = Query(None, description="Filter applications applied before this date"),
    last_updated_start: Optional[datetime] = Query(None, description="Filter applications updated after this date"),
    last_updated_end: Optional[datetime] = Query(None, description="Filter applications updated before this date"),
):
    # Build the base query
    query = (
        select(
            Application.status,
            Application.last_updated,
            func.count().label("count")
        )
        .where(Application.status.in_([ApplicationStatusEnum.IN_PROGRESS, ApplicationStatusEnum.APPLIED]))
        .group_by(Application.status, Application.last_updated)
    )
    # Apply filters based on query parameters
    
    if positions:
        query = query.where(Application.position_id.in_(positions))
    if applied_at_start:
        query = query.where(Application.applied_at >= applied_at_start)
    if applied_at_end:
        query = query.where(Application.applied_at <= applied_at_end)
    if last_updated_start:
        query = query.where(Application.last_updated >= last_updated_start)
    if last_updated_end:
        query = query.where(Application.last_updated <= last_updated_end)

    # Execute the query
    log.critical(query)
    results = db.exec(query)
    response = [{"status": row[0] , "count": row[1]} for row in results]

    return response



@app.get("/application_details/") 
async def application_details(current_user: UserDep,):
    pass

    

#----------------------START_UP-----------------------------
@app.on_event("startup")
def on_startup():
    # check connectivity
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
    # SQLModel.metadata.create_all(engine)

