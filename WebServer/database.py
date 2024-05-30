# from sqlalchemy import create_engine,MetaData,Table,Column
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.declarative import declarative_base
# import os
# # DataBase_URL=os.getenv('DATABASE_URL')
# Database_URL="http://localhost:6969/"
# engine=create_engine(Database_URL)
# SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)
# Base=declarative_base()
# metadata=MetaData()
from sqlalchemy import create_engine