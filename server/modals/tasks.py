from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TaskBase(BaseModel):
    text: Optional[str] = Field(None, description="Task name")
    priority: Optional[str] = Field(None, description="Task priority")
    task_description: Optional[str] = Field(
        None, description="Task description")
    start: Optional[datetime] = Field(None, description="Task start date")
    end: Optional[datetime] = Field(None, description="Task end date")
    parent: Optional[int] = Field(None, description="Parent task ID")
    assignee: Optional[str] = Field(None, description="Task assignee email")
    progress: Optional[float] = Field(
        None, description="Task progress percentage")
    type: Optional[str] = Field(None, description="Task type")
    open: Optional[bool] = Field(None, description="Whether task is open")
    status: Optional[str] = Field(None, description="Task status")
    progress: Optional[int] = Field(None, description="Task progress percentage")
    classification: Optional[str] = Field(
        None, description="Task classification")


class CreateTaskInputDataModel(TaskBase):
    project_id: str
    text: str
    task_description: str
    start: str
    end: str
    assignee: str
    parent: int
    progress: int
    type: str
    open: bool
    classification: str
    priority: str


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


class UpdateTaskModel(BaseModel):
    task_id: Optional[str] = Field(None, description="Task ID")
    project_id: Optional[str] = Field(None, description="Project ID")
    task: Optional[TaskBase] = Field(
        None, description="Task object with updated fields")
    links: Optional[List[dict]] = Field(
        None, description="Array of task links")


class CommentInputDataModel(BaseModel):
    task_id: str = Field(..., description="Task ID")
    content: str = Field(..., description="Comment content")
