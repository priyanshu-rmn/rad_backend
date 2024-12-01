from datetime import datetime
import json
from random import choice
from faker import Faker
from loguru import logger as log
from models import Application, ApplicationStatusEnum, DepartmentEnum, HiringStageNameEnum, PositionStatusEnum, StageStatusEnum

# Initialize Faker
faker = Faker()
users_data = []
positions_data = []
applications_data = []
stages_data = []

def save(data, path) :
    with open(path, "w") as json_file:
        json.dump(data, json_file, indent=4)

# Generate mock user data
def create_mock_users(n: int):
    for _ in range(n):
        user = {
            "id": faker.unique.random_int(min=1, max=1000),
            "name": faker.name(),
            "email": faker.unique.email(),
            "hashed_password": faker.sha256(),
        }
        users_data.append(user)
        
    save(users_data, "./mock/users.json")
 
# Generate mock user data
def create_mock_positions(n: int):
    for _ in range(n):
        user = {
            "id": faker.unique.random_int(min=1, max=1000),
            "title": faker.job(),
            "department": choice(list(DepartmentEnum)),
            "status": choice(list(PositionStatusEnum)), # TODO: 0 candidates accepted but position filled
            "created_at": faker.date_time_this_year().isoformat(),
        }
        positions_data.append(user)
        
    save(positions_data, "./mock/positions.json")
        

# Generate mock applications data
def create_mock_applications(n: int):
    for _ in range(n):
        candidate_id = choice(users_data)["id"]
        position_id = choice(positions_data)["id"]
        applied_at = faker.date_time_this_year()
        last_updated = faker.date_time_between(start_date=applied_at)
        
        last_stage_name = choice(list(HiringStageNameEnum) + [None])
                        
        if last_stage_name in [HiringStageNameEnum.RESUME_SCREENING, 
                                 HiringStageNameEnum.TEST_SCREENING, 
                                 HiringStageNameEnum.PHONE_SCREENING, 
                                 HiringStageNameEnum.TECHNICAL_INTERVIEW_1,
                                 HiringStageNameEnum.TECHNICAL_INTERVIEW_2]:
            status = choice([
                ApplicationStatusEnum.IN_PROGRESS,
                ApplicationStatusEnum.REJECTED,
                ApplicationStatusEnum.WITHDRAWN
            ])
        elif last_stage_name == HiringStageNameEnum.HR_MANAGERIAL_INTERVIEW:
            status = choice([
                ApplicationStatusEnum.OFFERED,
                ApplicationStatusEnum.REJECTED
            ])  
        elif last_stage_name == HiringStageNameEnum.OFFER_NEGOTIATION:
                status = choice([
                ApplicationStatusEnum.ACCEPTED,
                ApplicationStatusEnum.DECLINED
            ])  
        else:
            status=ApplicationStatusEnum.APPLIED
            

        application: Application = {
            "candidate_id": candidate_id,  
            "position_id": position_id,
            "applied_at": applied_at.isoformat(),
            "last_updated": last_updated.isoformat(),
            "status": status,
            "last_stage_name": last_stage_name,
        }
        
        # log.info(application)
        create_mock_stages(application)
        applications_data.append(application)
    
    # TODO: NUMBER_OF_OPENINGS FOR A POSITION. IN MOCK DATA x CANDIDATES MAY BE FILLED FOR A POSITION 
    save(applications_data, "./mock/applications.json")


def create_mock_stages(application : Application):
    hiring_stages = list(HiringStageNameEnum)
    
    if application["last_stage_name"] is None:
        return
    
    prev_updated = datetime.fromisoformat(application["applied_at"])
    last_updated = datetime.fromisoformat(application["last_updated"])
    
    for stage in hiring_stages:
        conducted_at, status = None, None
        if stage != application["last_stage_name"]:
            conducted_at = faker.date_time_between(start_date=prev_updated, end_date=last_updated)        
            status=StageStatusEnum.PASSED
        else :
            conducted_at = last_updated
            status=choice(list(StageStatusEnum))
            
        stage_entry = {
            "stage_name": stage,
            "candidate_id": application["candidate_id"],  
            "position_id": application["position_id"],
            "status": status,
            "conducted_at": conducted_at.isoformat(),
            "feedback" : faker.sentence() 
        }
        last_updated = conducted_at 
        
        stages_data.append(stage_entry) 
        if stage == application["last_stage_name"]:
            break
    
    save(stages_data, "./mock/stages.json")

if __name__ == "__main__":
    create_mock_users(50)
    create_mock_positions(25)
    create_mock_applications(100)
    
    print(len(users_data))
    print(len(positions_data))
    print(len(applications_data))
    print(len(stages_data))