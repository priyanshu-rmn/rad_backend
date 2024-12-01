from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel


# Enum for Position Status
class PositionStatusEnum(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    IN_PROGRESS = "in_progress"
    CANCELLED = "cancelled"
    FILLED = "filled"

# Enum for Application Status
class ApplicationStatusEnum(str, Enum):
    APPLIED = "applied"
    WITHDRAWN = "withdrawn"
    IN_PROGRESS = "in_progress"
    REJECTED = "rejected"
    OFFERED = "offered"
    ACCEPTED = "accepted"
    DECLINED = "declined"

# Enum for Hiring Stage Names
class HiringStageNameEnum(str, Enum):
    RESUME_SCREENING = "resume_screening"
    TEST_SCREENING = "test_screening"
    PHONE_SCREENING = "phone_screening"
    TECHNICAL_INTERVIEW_1 = "technical_interview_1"
    TECHNICAL_INTERVIEW_2 = "technical_interview_2"
    HR_MANAGERIAL_INTERVIEW = "hr_managerial_interview"
    OFFER_NEGOTIATION = "offer_negotiation"

# Enum for Stage Status
class StageStatusEnum(str, Enum):
    PASSED = "passed"
    FAILED = "failed"

# Enum for Departments
class DepartmentEnum(str, Enum):
    ENGINEERING = "Engineering"
    MARKETING = "Marketing"
    SALES = "Sales"
    HUMAN_RESOURCES = "Human Resources"
    FINANCE = "Finance"

# Application Table
class Application(SQLModel, table=True):
    __tablename__ = "applications"
    
    candidate_id: int = Field(foreign_key="users.id", primary_key=True)
    position_id: int = Field(foreign_key="positions.id", primary_key=True)
    applied_at: datetime = Field(default=None)
    last_updated: datetime = Field(default=None)
    
    status: ApplicationStatusEnum
    last_stage_name: Optional[HiringStageNameEnum] = Field(default=None)
    
    def __repr__(self):
        return f"Application(candidate_id={self.candidate_id}, position_id={self.position_id}, status={self.status}, last_stage_name={self.last_stage_name}, applied_at={self.applied_at}, last_updated={self.last_updated})"

      
        
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
    department: DepartmentEnum
    status: PositionStatusEnum
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship
    candidates: Optional[list["User"]] = Relationship(back_populates="applied_positions", link_model=Application)
    
    def __repr__(self):
        return f"Position(id={self.id}, title={self.title}, department={self.department}, status={self.status}, created_at={self.created_at})"

        
# Hiring Stages Table
class Stage(SQLModel, table=True):
    __tablename__ = "hiring_stages"
    
    stage_name: HiringStageNameEnum = Field(primary_key=True)
    candidate_id: int = Field(foreign_key="users.id", primary_key=True)
    position_id: int = Field(foreign_key="positions.id", primary_key=True)
    
    status: StageStatusEnum
    feedback: Optional[str] = Field(default=None)
    conducted_at: datetime
    
    def __repr__(self):
        return f"Stage(stage_name={self.stage_name}, candidate_id={self.candidate_id}, position_id={self.position_id}, status={self.status}, feedback={self.feedback}, conducted_at={self.conducted_at})"