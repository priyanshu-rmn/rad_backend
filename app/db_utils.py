from sqlalchemy import text
from sqlmodel import Session
from sqlalchemy.exc import SQLAlchemyError

def check_db_connection(db: Session):
    try:
        # Run a simple query to check connection
        db.exec(text("SELECT 1"))
        return ( {"flag":True, "status": "Connected to the database successfully!"})
    except SQLAlchemyError as e:
        return {"flag":False, "status": "Failed to connect to the database", "error": str(e)}
    finally:
        db.close()
        
        
