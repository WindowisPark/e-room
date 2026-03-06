from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.calendar import CalendarTask, CalendarGoal
from app.schemas.calendar import (
    CalendarTaskCreate, CalendarTaskOut,
    CalendarGoalCreate, CalendarGoalOut,
)

router = APIRouter()


class CalendarTaskUpdate(BaseModel):
    title: str


class CalendarGoalUpdate(BaseModel):
    title: str


# ── Tasks ──────────────────────────────────────────────

@router.get("/tasks", response_model=List[CalendarTaskOut])
def get_tasks(
    date: date,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return (
        db.query(CalendarTask)
        .filter(CalendarTask.user_id == current_user.id, CalendarTask.task_date == date)
        .order_by(CalendarTask.created_at)
        .all()
    )


@router.post("/tasks", response_model=CalendarTaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    body: CalendarTaskCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    task = CalendarTask(user_id=current_user.id, title=body.title, task_date=body.task_date)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# /tasks/dates 는 /tasks/{task_id} 보다 먼저 등록해야 "dates"가 task_id로 잡히지 않음
@router.get("/tasks/dates", response_model=List[str])
def get_task_dates(
    year: int,
    month: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    from sqlalchemy import extract
    rows = (
        db.query(CalendarTask.task_date)
        .filter(
            CalendarTask.user_id == current_user.id,
            extract("year", CalendarTask.task_date) == year,
            extract("month", CalendarTask.task_date) == month,
        )
        .distinct()
        .all()
    )
    return [str(r[0]) for r in rows]


@router.put("/tasks/{task_id}", response_model=CalendarTaskOut)
def update_task(
    task_id: int,
    data: CalendarTaskUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    task = db.query(CalendarTask).filter(
        CalendarTask.id == task_id,
        CalendarTask.user_id == current_user.id,
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
    task.title = data.title
    db.commit()
    db.refresh(task)
    return task


@router.patch("/tasks/{task_id}/toggle", response_model=CalendarTaskOut)
def toggle_task(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    task = db.query(CalendarTask).filter(
        CalendarTask.id == task_id, CalendarTask.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
    task.is_completed = not task.is_completed
    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    task = db.query(CalendarTask).filter(
        CalendarTask.id == task_id, CalendarTask.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
    db.delete(task)
    db.commit()


# ── Goals ──────────────────────────────────────────────

@router.get("/goals", response_model=List[CalendarGoalOut])
def get_goals(
    year: int,
    month: int,
    week: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return (
        db.query(CalendarGoal)
        .filter(
            CalendarGoal.user_id == current_user.id,
            CalendarGoal.year == year,
            CalendarGoal.month == month,
            CalendarGoal.week == week,
        )
        .order_by(CalendarGoal.created_at)
        .all()
    )


@router.post("/goals", response_model=CalendarGoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(
    body: CalendarGoalCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    goal = CalendarGoal(
        user_id=current_user.id,
        title=body.title,
        year=body.year,
        month=body.month,
        week=body.week,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.put("/goals/{goal_id}", response_model=CalendarGoalOut)
def update_goal(
    goal_id: int,
    data: CalendarGoalUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    goal = db.query(CalendarGoal).filter(
        CalendarGoal.id == goal_id,
        CalendarGoal.user_id == current_user.id,
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다.")
    goal.title = data.title
    db.commit()
    db.refresh(goal)
    return goal


@router.patch("/goals/{goal_id}/toggle", response_model=CalendarGoalOut)
def toggle_goal(
    goal_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    goal = db.query(CalendarGoal).filter(
        CalendarGoal.id == goal_id, CalendarGoal.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다")
    goal.is_completed = not goal.is_completed
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    goal = db.query(CalendarGoal).filter(
        CalendarGoal.id == goal_id, CalendarGoal.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다")
    db.delete(goal)
    db.commit()
