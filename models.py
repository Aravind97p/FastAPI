from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base  = declarative_base()

class Login(Base):
    __tablename__ = 'login'

    id  = Column(Integer, primary_key=True, index=True)
    email = Column(String)
    password = Column(String)
    created_on = Column(DateTime(timezone=True), server_default=func.now())
    updated_on = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), server_default=func.now())
    




