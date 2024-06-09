from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy import Column, Integer, String,TIMESTAMP,ForeignKey,Text,create_engine
import os
from dotenv import load_dotenv
from enum import Enum
load_dotenv()
db_user=os.getenv('POSTGRES_USER')
db_pass=os.getenv('POSTGRES_PASSWORD')
db_name=os.getenv('POSTGRES_DB')
db_host=os.getenv('POSTGRES_HOST')

Base=declarative_base()
class content_type(Enum):
    Blog='blog'
    social_media='social_media'
    tweet='tweet'
    story='story'

class User(Base):
    __tablename__="User"
    id=Column(Integer,primary_key=True,autoincrement=True)
    user_name=Column(String(100),unique=True)
    email=Column(String(100),unique=True)
    content=relationship("Content",backref="User") # one to many
    repurposed_content=relationship("Repurposed_Content",backref="User")
class Content(Base):
    __tablename__="Content"
    id=Column(Integer,primary_key=True,autoincrement=True)
    user_id=Column(Integer,ForeignKey('User.id'))
    title=Column(String(100))
    original_content=Column(Text)
    platform=relationship("Platform",backref="Content")
class Platform(Base):
    __tablename__="Platform"

    id=Column(Integer,primary_key=True,autoincrement=True)
    name=Column(String(100))

class Repurposed_Content(Base):
    __tablename__="Repurposed_Content"
    id=Column(Integer,primary_key=True,autoincrement=True)
    user_id=Column(Integer,ForeignKey('User.id'))
    content_id=Column(Integer,ForeignKey("Content.id"))
    title=Column(String(100))
    repurposed_content=Column(Text)
    platform=relationship("Platform",backref="Repurposed_Content")

DATABASE_URL = f"postgresql://{db_user}:{db_pass}@{db_host}:{6969}/{db_name}"
engine=create_engine(DATABASE_URL)
Session=sessionmaker(bind=engine,autocommit=False)
Base.metadata.create_all(bind=engine)