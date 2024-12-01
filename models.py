from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel


class PositionStatus(str, Enum):
    draft="draft"
    open="open"
    closed="closed"
    in_progess="in_progress"
    cancelled="cancelled"
    filled="filled"

class ApplicationStatus(str, Enum):
    applied="applied"
    withdrawn="withdrawn"
    in_progess="in_progress"
    rejected="rejected"
    offered="offered"
    accepted="accepted"
    declined="declined"

    
class HiringStage(str, Enum):
    resume_screening="resume_screening"       
    test_screening="test_screening"       
    phone_screening="phone_screening"       
    technical_interview_1="technical_interview_1"
    technical_interview_r="technical_interview_2"
    hr_managerial_interview="hr_managerial_interview"
    offer_negotiation="offer_negotiation"
    
class StageStatus(str, Enum):
    passed="passed"
    failed="failed"

# Application Table
class Application(SQLModel, table=True):
    __tablename__ = "applications"
    
    candidate_id: int = Field(foreign_key="users.id", primary_key=True)
    position_id: int = Field(foreign_key="positions.id", primary_key=True)
    applied_at: datetime = Field(default=None)
    last_updated: datetime = Field(default=None)
    
    status: ApplicationStatus
    last_stage_name: HiringStage
    
    def __repr__(self):
        return f"Application(candidate_id={self.candidate_id}, position_id={self.position_id}, status={self.status}, last_stage_name={self.last_stage_name}, applied_at={self.applied_at}, last_updated={self.last_updated})"

      
        
# models
class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str       
    email: str = Field(index=True)
    hashed_password: str
    
    applied_positions: Optional[list["Position"]] = Relationship(back_populates="candidates", link_model=Application)
    
    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, email={self.email})"
    

class Position(SQLModel, table=True):
    __tablename__ = "positions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=100)
    department: str = Field(max_length=100)
    status: PositionStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship
    candidates: Optional[list["User"]] = Relationship(back_populates="applied_positions", link_model=Application)
    
    def __repr__(self):
        return f"Position(id={self.id}, title={self.title}, department={self.department}, status={self.status}, created_at={self.created_at})"

        
# Hiring Stages Table
class Stage(SQLModel, table=True):
    __tablename__ = "hiring_stages"
    
    stage_name: HiringStage = Field(primary_key=True)
    candidate_id: int = Field(foreign_key="users.id", primary_key=True)
    position_id: int = Field(foreign_key="positions.id", primary_key=True)
    
    status: StageStatus
    feedback: Optional[str] = Field(default=None)
    conducted_at: datetime
    
    def __repr__(self):
        return f"Stage(stage_name={self.stage_name}, candidate_id={self.candidate_id}, position_id={self.position_id}, status={self.status}, feedback={self.feedback}, conducted_at={self.conducted_at})"