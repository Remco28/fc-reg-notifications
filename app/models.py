from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    date = Column(String, nullable=False)

    registrations = relationship("Registration", back_populates="tournament")


class Fencer(Base):
    __tablename__ = "fencers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)

    registrations = relationship("Registration", back_populates="fencer")


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    fencer_id = Column(Integer, ForeignKey("fencers.id"), nullable=False)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    events = Column(String, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    fencer = relationship("Fencer", back_populates="registrations")
    tournament = relationship("Tournament", back_populates="registrations")

    __table_args__ = (
        UniqueConstraint('fencer_id', 'tournament_id', name='unique_fencer_tournament'),
    )