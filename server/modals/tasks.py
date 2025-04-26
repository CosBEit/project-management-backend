from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TaskBase(BaseModel):
    text: str = Field(..., description="Task name")
    task_description: Optional[str] = Field(
        None, description="Task description")
    start: datetime = Field(..., description="Task start date")
    end: datetime = Field(..., description="Task end date")
    parent: int = Field(0, description="Parent task ID")
    assignee: str = Field(..., description="Task assignee email")
    progress: float = Field(0, description="Task progress percentage")
    type: str = Field("task", description="Task type")
    open: bool = Field(False, description="Whether task is open")
    classification: Optional[str] = Field(
        None, description="Task classification")


class CreateTaskInputDataModel(TaskBase):
    project_id: str = Field(..., description="Project ID")


class UpdateTaskInputDataModel(TaskBase):
    id: str = Field(..., description="Task ID")


class UpdateTaskDatesModel(BaseModel):
    id: str = Field(..., description="Task ID")
    start: Optional[datetime] = Field(None, description="New start date")
    end: Optional[datetime] = Field(None, description="New end date")
    duration: Optional[int] = Field(None, description="Duration in days")


class UpdateTaskStatusModel(BaseModel):
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    progress: float = Field(..., description="Task progress percentage")


class DeleteTaskInputDataModel(BaseModel):
    id: str = Field(..., description="Task ID")


class ProjectLinksInputDataModel(BaseModel):
    links: List[dict] = Field(..., description="List of task links")


class ManualInputDataModel(BaseModel):
    id: str = Field(..., description="Task ID")
    manual: str = Field(..., description="Task manual content")
    classification: str = Field(..., description="Task classification")


class ReportInputDataModel(BaseModel):
    id: str = Field(..., description="Task ID")
    report: str = Field(..., description="Task report content")
