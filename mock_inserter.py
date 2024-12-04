
import os
import json
from dotenv import load_dotenv
from pathlib import Path

from fastapi import FastAPI
from sqlmodel import SQLModel, Session, create_engine
from models import Application, DepartmentEnum, Position, PositionStatusEnum, Stage, User
from loguru import logger as log
load_dotenv(dotenv_path=Path(".env"))

app = FastAPI()
# Load JSON data from the file
def load_data(file_path: str):
    print
    with open(file_path, "r") as file:
        return json.load(file)

#----------------------Database connection-----------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

# Initialize Faker
USERS_MOCK_DATA=os.getenv("USERS_MOCK_DATA")
POSITIONS_MOCK_DATA=os.getenv("POSITIONS_MOCK_DATA")
APPLICATIONS_MOCK_DATA=os.getenv("APPLICATIONS_MOCK_DATA")
STAGES_MOCK_DATA=os.getenv("STAGES_MOCK_DATA")
DATABASE_URL = os.getenv("DATABASE_URL")


#using fastapi dependency
def insert_mock_users():
    log.critical("----------------------------Inserting Users----------------------------")
    data = load_data(USERS_MOCK_DATA)
    with Session(engine) as db:
        for user in data:
            new_user = User(
                id=user.get("id"),
                name=user.get("name"),
                email=user.get("email"),
                hashed_password=user.get("hashed_password"),
            )
            db.add(new_user)
        db.commit()

def insert_mock_positions():
    log.critical("----------------------------Inserting Positions----------------------------")
    data = load_data(POSITIONS_MOCK_DATA)
    with Session(engine) as db:
        for position in data:
            log.debug(position)
            new_position = Position(
                id=position.get("id"),
                title=position.get("title"),
                department=DepartmentEnum(position.get("department")),
                status=PositionStatusEnum(position.get("status")),
                created_at=position.get("created_at"),
            )
            log.debug(new_position)
            db.add(new_position)
        db.commit()


def insert_mock_applications():
    log.critical("----------------------------Inserting Applications----------------------------")
    data = load_data(APPLICATIONS_MOCK_DATA)
    with Session(engine) as db:
        for application in data:
            print(application)
            new_application = Application(
                candidate_id=application.get("candidate_id"),
                position_id=application.get("position_id"),
                applied_at=application.get("applied_at"),
                last_updated=application.get("last_updated"),
                status=application.get("status"),
                last_stage_name=application.get("last_stage_name"),
            )
            db.add(new_application)
        db.commit()

        
def insert_mock_stages():
    log.critical("----------------------------Inserting Stages----------------------------")
    data = load_data(STAGES_MOCK_DATA)
    with Session(engine) as db:
        for stage in data:
            new_stage = Stage(
                stage_name=stage.get("stage_name"),
                candidate_id=stage.get("candidate_id"),
                position_id=stage.get("position_id"),
                status=stage.get("status"),
                feedback=stage.get("feedback"),
                conducted_at=stage.get("conducted_at"),
            )
            db.add(new_stage)
        db.commit()

        
if __name__ =="__main__":
    SQLModel.metadata.create_all(engine)
    insert_mock_users()
    insert_mock_positions()
    insert_mock_applications()
    insert_mock_stages()
