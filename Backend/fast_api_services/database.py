from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DATABASE_URL = ("sqlite:///./users.db")

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'auth_users'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)

def init_db():
    Base.metadata.create_all(bind=engine)


class VideoDownload(Base):
    __tablename__ = 'video_downloads'

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, unique=True, index=True)
    file_name = Column(String)
    file_type = Column(String)
    download_status = Column(Float)

if __name__ == "__main__":
    init_db()