from sqlalchemy import create_engine, Column, Integer, String, DateTime  
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.orm import sessionmaker  
from datetime import datetime  

Base = declarative_base()  


class Article(Base):  
    __tablename__ = 'articles'  

    id = Column(Integer, primary_key=True)  
    user_id = Column(Integer)  
    file_path = Column(String)  
    status = Column(String)  # draft, review, approved, rejected  
    reviewer_id = Column(Integer, nullable=True)  
    publish_time = Column(DateTime, nullable=True)  
    created_at = Column(DateTime, default=datetime.utcnow)  

def get_db_url():  
    from dotenv import load_dotenv  
    import os  
    load_dotenv()  
    return f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"  

engine = create_engine(get_db_url())  
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  

Base.metadata.create_all(bind=engine)  
