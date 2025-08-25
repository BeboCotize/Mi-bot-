from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Base, User

engine = create_engine("sqlite:///users.db")
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

def add_user(user_id: int):
    session = Session()
    if not session.query(User).filter_by(id=user_id).first():
        user = User(id=user_id)
        session.add(user)
        session.commit()
    session.close()

def is_user_registered(user_id: int) -> bool:
    session = Session()
    exists = session.query(User).filter_by(id=user_id).first() is not None
    session.close()
    return exists