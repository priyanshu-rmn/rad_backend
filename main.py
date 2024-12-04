from datetime import datetime
import os
from typing import Annotated, Optional 
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import SQLModel, Session, create_engine, select
from loguru import logger as log

from KPIs import get_all_positions, get_application_status_data, get_candidate_stage_data, get_recent_applications_count, get_time_to_hire_all_depts
from auth import create_access_token, hash_password, verify_access_token, verify_password
from db_utils import check_db_connection
from models import Application, ApplicationStatusEnum, DepartmentEnum, PositionStatusEnum, User, Position     

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
engine = create_engine(DATABASE_URL)


#using fastapi dependency
def get_session():
    with Session(engine) as db:
        yield db
        
SessionDep = Annotated[Session, Depends(get_session)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/")
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
    username: str
    password: str
    
@app.post("/register/")
def register(user: Credentials, db: SessionDep):
    log.info("Registering ...", Credentials)
    db_user = db.exec(select(User).where(User.email == user.username)).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="email already registered",
        )
    hashed_password = hash_password(user.password)
    new_user = User(name="admin", email=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

@app.post("/login/", )
async def login(user:Credentials, db: SessionDep):
    log.info("Logging in ...", user)
    db_user = db.exec(select(User).where(User.email == user.username)).first()
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


@app.get("/dashboard/")
async def get_dashboard_data(
    db: SessionDep,
    current_user: UserDep,
    positions: Optional[list[int]] = Query(None, description="Filter by position IDs", alias="positions[]"),
    departments: Optional[list[str]] = Query(None, description="Filter by department IDs", alias="departments[]"),
    start_date: Optional[datetime] = Query(None, description="Filter data after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter data before this date"),
):
    filters = {
        "position_id": positions,
        "departments": departments,
        "start_date": start_date,
        "end_date": end_date,
    }
    log.debug(current_user)
    print(filters)

    if(departments is None) :
        filters["departments"] = [department.value for department in DepartmentEnum]
    
    if start_date is None :
        filters["start_date"] = datetime.min

    if end_date is None :
        filters["end_date"] = datetime.max

    all_positions = get_all_positions(db);
    if positions is None:
        filters["position_id"] = list(all_positions.keys())

    print(filters)

    all_application_status = get_application_status_data(db, filters); 

    response = {
        'all_positions': all_positions,
        'all_departments' : [department.value for department in DepartmentEnum],
        'candidate_stage_counts': get_candidate_stage_data(db, filters),
        'depts_time_to_hire': get_time_to_hire_all_depts(db, filters),
        'offer_status': {"OFFER_ACCEPTED" : all_application_status.get("ACCEPTED",0), "OFFER_DECLINED": all_application_status.get("DECLINED",0), "OFFER_PENDING": all_application_status.get("OFFERED",0)},
        'application_status_count' : {"WAITING": all_application_status.get("IN_PROGRESS",0), "NO_ACTION": all_application_status.get("APPLIED",0), "NEW_APPLICANTS":get_recent_applications_count(db, filters)}
    }
    response['candidate_stage_counts'] = {
        "TOTAL_APPLICATIONS": response['candidate_stage_counts'].get("RESUME_SCREENING", 0) + all_application_status.get("APPLIED",0),
        **response['candidate_stage_counts']  # Unpacking the rest of the items
    }

    return response
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


# @app.get("/time_to_fill/")
# async def time_to_fill(
#     db: SessionDep,
#     current_user: UserDep,
#     start_date: Optional[datetime] = Query(None, description="Filter positions created after this date"),
#     end_date: Optional[datetime] = Query(None, description="Filter positions created before this date"),
# ):
#     log.info(current_user);
    
#     # Build the base query
#     query = select(Position).where(Position.status == PositionStatusEnum.FILLED)

#     # Apply start_date filter if provided
#     if start_date:
#         query = query.where(Position.created_at >= start_date)

#     # Apply end_date filter if provided
#     if end_date:
#         query = query.where(Position.created_at <= end_date)

#     # Execute the query and fetch results
#     results = db.exec(query).all()

#     return results



# @app.get("/time_to_hire/")
# async def time_to_hire(
#     db: SessionDep,
#     current_user: UserDep,
    
# ):
#     pass


# @app.get("/candidate_pipeline/")
# async def candidate_pipeline_metric(
#     db: SessionDep,
#     # current_user: UserDep,
#     application_status: Optional[list[str]] = Query(None, description="Filter by application status"),
#     positions: Optional[list[int]] = Query(None, description="Filter by position IDs"),
#     applied_at_start: Optional[datetime] = Query(None, description="Filter applications applied after this date"),
#     applied_at_end: Optional[datetime] = Query(None, description="Filter applications applied before this date"),
#     last_updated_start: Optional[datetime] = Query(None, description="Filter applications updated after this date"),
#     last_updated_end: Optional[datetime] = Query(None, description="Filter applications updated before this date"),
# ):
#     print(application_status)
#     # Build the base query
#     query = (
#         select(
#             Application.last_stage_name,
#             func.count().label("count")
#         )
#         .group_by(Application.last_stage_name)
#     )
#     # Apply filters based on query parameters
#     if application_status:
#         query = query.where(Application.status.in_(application_status))
#     if positions:
#         query = query.where(Application.position_id.in_(positions))
#     if applied_at_start:
#         query = query.where(Application.applied_at >= applied_at_start)
#     if applied_at_end:
#         query = query.where(Application.applied_at <= applied_at_end)
#     if last_updated_start:
#         query = query.where(Application.last_updated >= last_updated_start)
#     if last_updated_end:
#         query = query.where(Application.last_updated <= last_updated_end)

#     # Execute the query
#     log.critical(query)
#     results = db.exec(query)
    
#     response = [{"last_stage_name": row[0] if row[0] else "YET_TO_START", "count": row[1]} for row in results]

#     return response
    

# @app.get("/offer_details/")
# async def offer_details(
#     db: SessionDep,
#     # current_user: UserDep,
#     positions: Optional[list[int]] = Query(None, description="Filter by position IDs"),
#     applied_at_start: Optional[datetime] = Query(None, description="Filter applications applied after this date"),
#     applied_at_end: Optional[datetime] = Query(None, description="Filter applications applied before this date"),
#     last_updated_start: Optional[datetime] = Query(None, description="Filter applications updated after this date"),
#     last_updated_end: Optional[datetime] = Query(None, description="Filter applications updated before this date"),
# ):
#     # Build the base query
#     query = (
#         select(
#             Application.status,
#             func.count().label("count")
#         )
#         .where(Application.status.in_([ApplicationStatusEnum.OFFERED, ApplicationStatusEnum.ACCEPTED, ApplicationStatusEnum.DECLINED]))
#         .group_by(Application.status)
#     )
#     # Apply filters based on query parameters
    
#     if positions:
#         query = query.where(Application.position_id.in_(positions))
#     if applied_at_start:
#         query = query.where(Application.applied_at >= applied_at_start)
#     if applied_at_end:
#         query = query.where(Application.applied_at <= applied_at_end)
#     if last_updated_start:
#         query = query.where(Application.last_updated >= last_updated_start)
#     if last_updated_end:
#         query = query.where(Application.last_updated <= last_updated_end)

#     # Execute the query
#     log.critical(query)
#     results = db.exec(query)
#     response = [{"status": row[0] , "count": row[1]} for row in results]

#     return response
    

# @app.get("/candidate_waiting_noaction_new/")
# async def candidates_waiting(  
#     db: SessionDep,                             
#     # current_user: UserDep,
#     positions: Optional[list[int]] = Query(None, description="Filter by position IDs"),
#     applied_at_start: Optional[datetime] = Query(None, description="Filter applications applied after this date"),
#     applied_at_end: Optional[datetime] = Query(None, description="Filter applications applied before this date"),
#     last_updated_start: Optional[datetime] = Query(None, description="Filter applications updated after this date"),
#     last_updated_end: Optional[datetime] = Query(None, description="Filter applications updated before this date"),
# ):
#     # Build the base query
#     query = (
#         select(
#             Application.status,
#             Application.last_updated,
#             func.count().label("count")
#         )
#         .where(Application.status.in_([ApplicationStatusEnum.IN_PROGRESS, ApplicationStatusEnum.APPLIED]))
#         .group_by(Application.status, Application.last_updated)
#     )
#     # Apply filters based on query parameters
    
#     if positions:
#         query = query.where(Application.position_id.in_(positions))
#     if applied_at_start:
#         query = query.where(Application.applied_at >= applied_at_start)
#     if applied_at_end:
#         query = query.where(Application.applied_at <= applied_at_end)
#     if last_updated_start:
#         query = query.where(Application.last_updated >= last_updated_start)
#     if last_updated_end:
#         query = query.where(Application.last_updated <= last_updated_end)

#     # Execute the query
#     log.critical(query)
#     results = db.exec(query)
#     response = [{"status": row[0] , "count": row[1]} for row in results]

#     return response



# @app.get("/application_details/") 
# async def application_details(current_user: UserDep,):
#     pass

    

