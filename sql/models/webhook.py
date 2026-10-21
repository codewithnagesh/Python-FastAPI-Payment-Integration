from database import Base
from sqlalchemy import Column, Integer, String


class Webhook(Base):
    __tablename__ = "webhooks"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(String, nullable=False)
