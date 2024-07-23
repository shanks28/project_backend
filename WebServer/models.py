from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy import Column, Integer, String,ForeignKey,Text,create_engine
import os
from dotenv import load_dotenv
from enum import Enum
from sqlalchemy import Enum as enumColumn
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
    content=relationship("Content",backref="User") # one to many
    repurposed_content=relationship("Repurposed_Content",backref="User")
class Content(Base):
    __tablename__="Content"
    id=Column(Integer,primary_key=True,autoincrement=True)
    user_id=Column(Integer,ForeignKey('User.id'))
    p_name=Column(String(100),ForeignKey('Platform.name'))
    title=Column(String(100))
    original_content=Column(Text)
    post_type=Column(enumColumn(content_type,default=content_type.Blog))
    platform=relationship("Platform",backref="Content")
class Platform(Base):
    __tablename__="Platform"

    name=Column(String(100),primary_key=True)

class Repurposed_Content(Base):
    __tablename__="Repurposed_Content"
    id=Column(Integer,primary_key=True,autoincrement=True)
    user_id=Column(Integer,ForeignKey('User.id'))
    p_name=Column(String(100),ForeignKey('Platform.name'))
    content_id=Column(Integer,ForeignKey("Content.id"))
    title=Column(String(100))
    repurposed_content=Column(Text)
    platform=relationship("Platform",backref="Repurposed_Content")



def get_session():
    data_base_url = f"postgresql://{db_user}:{db_pass}@db:5432/{db_name}"
    engine = create_engine(data_base_url)
    Session = sessionmaker(bind=engine, autocommit=False)
    Base.metadata.create_all(bind=engine)
    return Session()