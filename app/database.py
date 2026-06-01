import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Read DB URL but don't assume immediate availability of native drivers.
DATABASE_URL = os.getenv('DATABASE_URL')

# Lazily create engine; if creation/driver triggers errors, set engine to None
engine = None
SessionLocal = None
try:
    if DATABASE_URL:
        # SQLAlchemy needs special handling for psycopg2 connection kwargs
        connect_args = {
            'connect_timeout': 10,
            'application_name': 'productmgr'
        }
        engine = create_engine(
            DATABASE_URL, 
            connect_args=connect_args,
            pool_pre_ping=True,
            echo=False
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    else:
        logging.warning('DATABASE_URL not set; database disabled.')
except Exception:
    logging.exception('Failed creating SQLAlchemy engine; database unavailable. Continuing without DB.')

Base = declarative_base()
