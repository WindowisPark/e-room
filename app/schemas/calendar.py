from datetime import date, datetime
from pydantic import BaseModel


class CalendarTaskCreate(BaseModel):
    title: str
    task_date: date


class CalendarTaskOut(BaseModel):
    id: int
    title: str
    task_date: date
    is_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CalendarGoalCreate(BaseModel):
    title: str
    year: int
    month: int
    week: int


class CalendarGoalOut(BaseModel):
    id: int
    title: str
    year: int
    month: int
    week: int
    is_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True
