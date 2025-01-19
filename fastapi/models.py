from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from config import Base

class User(Base):
    __tablename__ = "USER"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    age = Column(Integer)
    gender = Column(Boolean)
    weight = Column(Float)
    height = Column(Float)
    bmi = Column(Float)
    drinking_status = Column(Boolean)
    smoking_status = Column(Boolean)
    obesity_status = Column(Boolean)
    fatigue_status = Column(Boolean)

    details = relationship("Detail", back_populates="user")
    videos = relationship("Video", back_populates="user")
    tvs = relationship("TV", back_populates="user")

class Detail(Base):
    __tablename__ = "DETAIL"

    detail_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("USER.user_id"))
    systolic_bp = Column(Integer)
    diastolic_bp = Column(Integer)
    heart_rate = Column(Integer)
    daily_steps = Column(Integer)
    cholesterol_status = Column(Boolean)
    daily_sleep = Column(Float)
    hypertension_status = Column(Boolean)

    user = relationship("User", back_populates="details")

class Video(Base):
    __tablename__ = "VIDEO"

    video_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("USER.user_id"))
    title = Column(String(50))
    video_length = Column(Integer)
    viewing_time = Column(Integer)
    category = Column(String(20))

    user = relationship("User", back_populates="videos")

class TV(Base):
    __tablename__ = "TV"

    iptv_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("USER.user_id"))

    user = relationship("User", back_populates="tvs")
