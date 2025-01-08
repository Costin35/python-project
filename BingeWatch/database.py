from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "postgresql://username:password12345@localhost:5557/tvshowsdb"

engine = create_engine(DATABASE_URL)

Base = declarative_base()

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize the database by creating all defined tables.

    This function inspects all SQLAlchemy models (classes inheriting from Base)
    and creates the corresponding tables in the database if they do not already exist.
    """
    Base.metadata.create_all(bind=engine)


class Show(Base):
    __tablename__ = 'shows'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    imdb_link = Column(String, nullable=False, unique=True)
    last_watched_season = Column(Integer, nullable=False)
    last_watched_episode = Column(Integer, nullable=False)
    last_watched_date = Column(String, nullable=True)
    score = Column(Float, nullable=False, default=0.0)
    snoozed = Column(Boolean, nullable=False, default=False)

    trailers = relationship("Trailer", back_populates="tv_show")
    uploads = relationship("Upload", back_populates="tv_show")

class Trailer(Base):
    __tablename__ = 'trailers'
    id = Column(Integer, primary_key=True, index=True)
    show_id = Column(Integer, ForeignKey('shows.id'), nullable=False)
    url = Column(String, nullable=False)
    is_new = Column(Boolean, nullable=False, default=True)

    tv_show = relationship("Show", back_populates="trailers")

class Upload(Base):
    __tablename__ = 'uploads'
    id = Column(Integer, primary_key=True, index=True)
    show_id = Column(Integer, ForeignKey('shows.id'), nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    is_new = Column(Boolean, nullable=False, default=True)

    tv_show = relationship("Show", back_populates="uploads")
