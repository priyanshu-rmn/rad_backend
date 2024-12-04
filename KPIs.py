from collections import defaultdict
from sqlmodel import Session, case, cast, select, func, Float, text

from models import Application, ApplicationStatusEnum, Position, Stage

def get_all_positions(db):
    results = db.exec(select(Position.title, Position.id)).all()
    return {id: title for title, id in results}
    

def get_candidate_stage_data(db: Session, filters):

    results = db.exec(
        select(Stage.stage_name, func.count().label("count"))
        .join(Position, Stage.position_id == Position.id)  # Joining Stage and Position
        .filter(
            Position.department.in_(filters["departments"]),
            Position.id.in_(filters["position_id"]),
            Stage.conducted_at >= filters["start_date"],
            Stage.conducted_at <= filters["end_date"]
        )
        .group_by(Stage.stage_name)
    ).all()

    return {stage: count for stage, count in results}


def get_time_to_hire_all_depts(db, filters):
    results = db.exec(
        select(
            Position.department,
            func.avg(
                cast(
                    func.extract('epoch', Application.last_updated - Application.applied_at) / 86400,  # Convert seconds to days
                    Float
                )
            ).label("avg_days")
        )
        .join(Position, Position.id == Application.position_id)
        .where(Application.status == ApplicationStatusEnum.ACCEPTED)
        .filter(
            Position.department.in_(filters["departments"]),
            Position.id.in_(filters["position_id"]),
            Application.applied_at >= filters["start_date"],
            Application.last_updated <= filters["end_date"]
        )
        .group_by(Position.department)
    ).all()
    
    return {department: avg_duration for department, avg_duration in results}


def get_application_status_data(db, filters) :
    results = db.exec (
        select(Application.status, func.count().label("count"))
        .join(Position, Application.position_id == Position.id)  # Joining Stage Position
        .filter(
            Position.department.in_(filters["departments"]),
            Position.id.in_(filters["position_id"]),
            Application.applied_at >= filters["start_date"],
            Application.applied_at <= filters["end_date"]
        )
        .group_by(Application.status)
    ).all()
    print(results)

    return {status : count for status, count in results}

def get_recent_applications_count(db: Session, filters):

    recent_count = db.exec(
        select(func.count()).
        select_from(Application)        
        .join(Position, Application.position_id == Position.id)  # Joining Stage Position
        .where(Application.applied_at >= func.now() - text("interval '7 days'"))
        .filter(
            Position.department.in_(filters["departments"]),
            Position.id.in_(filters["position_id"]),
            Application.applied_at >= filters["start_date"],
            Application.applied_at <= filters["end_date"]
        )
    ).one()
    
    return recent_count


def application_per_job_posting(db: Session, filters) :
    results = db.exec(
    select(
        Position.title,
        func.to_char(Application.applied_at, 'YYYY-MM-DD').label('day'),  # Correct usage of to_char with the timestamp
        func.count().label('application_count')
    )
    .join(Position, Application.position_id == Position.id)
    .filter(
        Position.department.in_(filters["departments"]),
        Position.id.in_(filters["position_id"]),
        Application.applied_at >= filters["start_date"],
        Application.applied_at <= filters["end_date"]
    )
    .group_by(Position.title, func.to_char(Application.applied_at, 'YYYY-MM-DD'))
    ).all()

    res = defaultdict(dict)
    for title, time , count in results:
        res[title][time] = count
        

    return res
