from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy import Column, Integer, String,TIMESTAMP,ForeignKey,Text,create_engine
import os
from dotenv import load_dotenv
load_dotenv()
db_user=os.getenv('POSTGRES_USER')
db_pass=os.getenv('POSTGRES_PASSWORD')
db_name=os.getenv('POSTGRES_DB')
db_host=os.getenv('POSTGRES_HOST')

Base=declarative_base()
class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True,autoincrement=True)
    user_name=Column(String(100),unique=True)
    email=Column(String(100),unique=True)
    # platform=relationship("Platform",back_populates="users")

# class Platform(Base):
#     __tablename__="platform"
#
#     id=Column(Integer,primary_key=True,autoincrement=True)
#     user_id=Column(Integer,ForeignKey("users.id"))
#     platform=Column(String(100))
#     user=relationship("User",back_populates="platform")
#     posts=relationship("Post",back_populates="platform")
#
# class Posts(Base):
#     __tablename__="posts"
#     id=Column(Integer,primary_key=True,autoincrement=True)
#     platform_id=Column(Integer,ForeignKey('platform.id'))
#     title=Column(String(100))
#     content=Column(Text)
#     platform=relationship("Platform",back_populates="posts")
#     user=relationship("RepurposedText",back_populates="posts")
# class RepurposedText(Base):
#     __table__name="repurposedtext"
#     id=Column(Integer,primary_key=True,autoincrement=True)
#     platform_id=Column(Integer,ForeignKey('platform.id'))
#     content_category=Column(String(100))
#     content=Column(Text)
#     post=relationship("Post",back_populates="repurposedtext")
DATABASE_URL = f"postgresql://{db_user}:{db_pass}@{db_host}:{6969}/{db_name}"
engine=create_engine(DATABASE_URL)
Session=sessionmaker(bind=engine,autocommit=False)
Base.metadata.create_all(bind=engine)