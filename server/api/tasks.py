from os import link
import uuid
import traceback
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from server.modals.tasks import (
    CreateTaskInputDataModel,
    UpdateTaskInputDataModel,
    UpdateTaskDatesModel,
    UpdateTaskModel,
    UpdateTaskStatusModel,
    DeleteTaskInputDataModel,
    ProjectLinksInputDataModel,
    ManualInputDataModel,
    ReportInputDataModel
)
from server.dependencies.auth import OAuth2PasswordBearerWithCookie
from server.configs.db import tasks_collection, links_collection, projects_collection

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/api/v1/auth/login")


@router.post("/tasks")
async def create_task(
    task_data: CreateTaskInputDataModel,
    current_user: dict = Depends(oauth2_scheme),
):
    """Create a new task.

    Args:
        task_data (CreateTaskInputDataModel): The task's data including 
        text, task_description, start, end, parent, assignee, and progress.
        current_user (dict): The current authenticated user.
        db: Database connection.

    Returns:
        dict: The created task.

    Raises:
        HTTPException: If the user is not authorized or an error occurs.
    """
    try:
        # Check if the current user is an admin
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create tasks"
            )

        # Create a new task document
        _id = str(uuid.uuid4())

        new_task = {
            "_id": _id,
            "project_id": task_data.project_id,
            "text": task_data.text,
            "task_description": task_data.task_description,
            "start": datetime.combine(task_data.start, datetime.min.time()),
            "end": datetime.combine(task_data.end, datetime.max.time()),
            "base_start": datetime.combine(task_data.start, datetime.min.time()),
            "base_end": datetime.combine(task_data.end, datetime.max.time()),
            "assignee": task_data.assignee,
            "parent": task_data.parent,
            "progress": task_data.progress,
            "classification": task_data.classification,
            "type": task_data.type,
            "open": task_data.open,
            "created_at": datetime.now(),
            "status": "not_started",
            "created_by": current_user["email"]
        }

        await tasks_collection.insert_one(new_task)

        return {"message": "Task created successfully", "unique_id": _id}

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.get("/tasks")
async def get_tasks(
    project_id: str,
    current_user: dict = Depends(oauth2_scheme),
):
    """Get all tasks for a specific project.

    Args:
        project_id (str): The ID of the project to retrieve tasks for.
        current_user (dict): The current authenticated user.
        db: Database connection.

    Returns:
        dict: A dictionary containing the list of tasks and project name.

    Raises:
        HTTPException: If the user is not authorized or an error occurs.
    """
    try:
        # Check if the current user is an admin
        if current_user["role"] != "admin":

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You do not have permission to perform this action."
            )

        # Get project details
        print("project_id", project_id)
        project = await projects_collection.find_one(
            {"_id": project_id},
            {"project_name": 1}
        )
        print("project", project)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        project_name = project.get("project_name", "Unknown Project")

        # Retrieve all tasks for the specified project
        tasks = await tasks_collection.find(
            {"project_id": project_id},
            {
                "_id": 1,
                "text": 1,
                "task_description": 1,
                "start": 1,
                "base_start": 1,
                "end": 1,
                "base_end": 1,
                "parent": 1,
                "assignee": 1,
                "progress": 1,
                "created_at": 1,
                "created_by": 1,
                "type": 1,
                "classification": 1,
                "status": 1,
                "open": 1
            }
        ).to_list(length=None)

        # Convert datetime objects to date strings
        print("tasks", tasks)
        for task in tasks:
            if "created_at" in task and "start" in task and "end" in task:
                task["start"] = task["start"].date().isoformat()
                task["end"] = datetime.combine(
                    task["end"].date(), datetime.max.time()).isoformat()
                task["base_start"] = task["base_start"].date().isoformat()
                task["base_end"] = datetime.combine(
                    task["base_end"].date(), datetime.max.time()).isoformat()
                task["created_at"] = task["created_at"].date().isoformat()
                task["id"] = task["_id"]
                del task["_id"]

        return {
            "project_name": project_name,
            "tasks": tasks
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


# @router.get("/tasks/{task_id}")
# async def get_task(
#     task_id: str,
#     current_user: dict = Depends(oauth2_scheme),
# ):
#     """Get a specific task by ID.

#     Args:
#         task_id (str): The ID of the task to retrieve.
#         current_user (dict): The current authenticated user.
#         db: Database connection.

#     Returns:
#         dict: The task details.

#     Raises:
#         HTTPException: If the task is not found or an error occurs.
#     """
#     try:
#         task = await tasks_collection.find_one(
#             {"_id": task_id},
#             {
#                 "_id": 1,
#                 "text": 1,
#                 "task_description": 1,
#                 "start": 1,
#                 "end": 1,
#                 "parent": 1,
#                 "assignee": 1,
#                 "progress": 1,
#                 "created_at": 1,
#                 "created_by": 1,
#                 "type": 1,
#                 "classification": 1,
#                 "status": 1,
#                 "open": 1
#             }
#         )


#         # Convert datetime objects to date strings
#         if "created_at" in task and "start" in task and "end" in task:
#             task["start"] = task["start"].date().isoformat()
#             task["end"] = task["end"].date().isoformat()
#             task["created_at"] = task["created_at"].date().isoformat()

#         task["id"] = task["_id"]
#         del task["_id"]

#         return task

#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         traceback.print_exc()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=str(e)
#         ) from e


# @router.put("/tasks/{task_id}")
# async def update_task(
#     task_id: str,
#     task_data: UpdateTaskInputDataModel,
#     current_user: dict = Depends(oauth2_scheme),
# ):
#     """Update an existing task.

#     Args:
#         task_id (str): The ID of the task to update.
#         task_data (UpdateTaskInputDataModel): The updated task data.
#         current_user (dict): The current authenticated user.
#         db: Database connection.

#     Returns:
#         dict: The updated task.

#     Raises:
#         HTTPException: If the user is not authorized, the task is not found, or an error occurs.
#     """
#     try:
#         # Check if the current user is an admin
#         if current_user["role"] != "admin":
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Only admins can update tasks"
#             )

#         # Find the task to update
#         task = await tasks_collection.find_one({"_id": task_id})

#         # Prepare the update data
#         update_data = {
#             "text": task_data.text,
#             "task_description": task_data.task_description,
#             "start": datetime.combine(task_data.start, datetime.min.time()),
#             "end": datetime.combine(task_data.end, datetime.max.time()),
#             "assignee": task_data.assignee,
#             "classification": task_data.classification,
#             "updated_at": datetime.now(),
#             "updated_by": current_user["email"]
#         }

#         # Update the task
#         await tasks_collection.update_one(
#             {"_id": task_id},
#             {"$set": update_data}
#         )

#         # Get the updated task
#         updated_task = await tasks_collection.find_one({"_id": task_id})

#         # Convert datetime objects to date strings
#         if "created_at" in updated_task and "start" in updated_task and "end" in updated_task:
#             updated_task["start"] = updated_task["start"].date().isoformat()
#             updated_task["end"] = updated_task["end"].date().isoformat()
#             updated_task["created_at"] = updated_task["created_at"].date(
#             ).isoformat()

#         updated_task["id"] = updated_task["_id"]
#         del updated_task["_id"]

#         return updated_task

#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         traceback.print_exc()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=str(e)
#         ) from e


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    current_user: dict = Depends(oauth2_scheme),
):
    """Delete a task and its children, along with associated links.

    Args:
        task_id (str): The ID of the task to delete.
        current_user (dict): The current authenticated user.
        db: Database connection.

    Returns:
        dict: A message indicating the deletion status.

    Raises:
        HTTPException: If the user is not authorized, the task is not found, or an error occurs.
    """
    try:
        # Check if the current user is an admin
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can delete tasks"
            )

        # Get the task to be deleted to check its parent
        task_to_delete = await tasks_collection.find_one({"_id": task_id})

        parent_id = task_to_delete.get("parent", 0)

        # Get all tasks to be deleted (parent and children)
        tasks_to_delete = []
        tasks_to_delete.append(task_id)  # Add parent task

        # Find all child tasks recursively
        async def find_child_tasks(parent_id):
            children = await tasks_collection.find({"parent": parent_id}).to_list(length=None)
            for child in children:
                tasks_to_delete.append(child["_id"])
                await find_child_tasks(child["_id"])

        # Find all child tasks if the task exists
        await find_child_tasks(task_id)

        # Delete all links where source or target is in tasks_to_delete
        await links_collection.update_many(
            {},
            {"$pull": {"links": {"$or": [
                {"source": {"$in": tasks_to_delete}},
                {"target": {"$in": tasks_to_delete}}
            ]}}}
        )

        # Delete all tasks (parent and children)
        delete_result = await tasks_collection.delete_many({
            "_id": {"$in": tasks_to_delete}
        })

        # If the deleted task had a parent, check if parent has other children
        if parent_id != 0:
            other_children = await tasks_collection.count_documents({
                "parent": parent_id,
                "_id": {"$ne": task_id}
            })
            if other_children == 0:
                # No other children, set parent's open to false
                await tasks_collection.update_one(
                    {"_id": parent_id},
                    {"$set": {"open": False}}
                )

        return {"message": f"Successfully deleted {delete_result.deleted_count} tasks and their associated links"}

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.post("/tasks/links")
async def create_or_update_links(
    link_data: ProjectLinksInputDataModel,
    current_user: dict = Depends(oauth2_scheme),
):
    """Create or update links between tasks.

    Args:
        link_data (ProjectLinksInputDataModel): The link data.
        current_user (dict): The current authenticated user.

    Returns:
        JSONResponse: A response indicating the update status.

    Raises:
        HTTPException: If the user is not authorized or an error occurs.
    """
    try:
        # Check if the current user is an admin
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action."
            )

        # Convert LinkDataModel objects to dictionaries and add a unique ID
        links_as_dicts = [
            {**link, "id": str(uuid.uuid4())} for link in link_data.links
        ]

        # Check if a document for links already exists
        existing_links = await links_collection.find_one({})

        if existing_links:
            # Update the existing document
            await links_collection.update_one(
                {},
                {"$set": {"links": links_as_dicts}}
            )
        else:
            # Create a new document
            new_links = {
                "_id": str(uuid.uuid4()),
                "links": links_as_dicts
            }
            await links_collection.insert_one(new_links)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Links updated successfully"}
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.get("/tasks/links")
async def get_links(
    project_id: str,
    current_user: dict = Depends(oauth2_scheme),
):
    """Get all links between tasks for a specific project.

    Args:
        project_id (str): The ID of the project to retrieve links for.
        current_user (dict): The current authenticated user.

    Returns:
        JSONResponse: A response containing the links.

    Raises:
        HTTPException: If the user is not authorized or an error occurs.
    """
    try:
        # Check if the current user is an admin
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You do not have permission to perform this action."
            )

        # Retrieve the links
        links = await links_collection.find_one(
            {"project_id": project_id},
            {"_id": 1, "links": 1}
        )

        if not links:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"links": []}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=links
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.put("/tasks/update-dates")
async def update_task_dates(
    task_data: UpdateTaskDatesModel,
    current_user: dict = Depends(oauth2_scheme),
):
    """Update the start and end dates of an existing task.

    Args:
        task_data (UpdateTaskDatesModel): The task date update data.
        current_user (dict): The current authenticated user.

    Returns:
        JSONResponse: A response indicating the update status.

    Raises:
        HTTPException: If the user is not authorized, the task is not found, or an error occurs.
    """
    try:
        # Check if the current user is an admin
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action."
            )

        # Find the task to update
        task = await tasks_collection.find_one({"_id": task_data.id})

        # Prepare the update data
        update_data = {}
        if task_data.start is not None:
            update_data["start"] = task_data.start
        if task_data.end is not None:
            update_data["end"] = task_data.end
        if task_data.duration is not None:
            update_data["duration"] = task_data.duration

        # Update the task's dates
        if update_data:
            await tasks_collection.update_one(
                {"_id": task_data.id},
                {"$set": update_data}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Task dates updated successfully"}
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.post("/tasks/manual")
async def create_or_update_manual(
    manual_data: ManualInputDataModel,
    current_user: dict = Depends(oauth2_scheme),
):
    """Create or update a manual for a specific task.

    Args:
        manual_data (ManualInputDataModel): The manual data.
        current_user (dict): The current authenticated user.

    Returns:
        JSONResponse: A response indicating the update status.

    Raises:
        HTTPException: If the user is not authorized or an error occurs.
    """
    try:
        # Check if the current user is an admin
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action."
            )

        # Check if a manual for the task already exists
        task_exists = await tasks_collection.find_one({"_id": manual_data.id})

        if task_exists:
            # Update the existing manual
            await tasks_collection.update_one(
                {"_id": manual_data.id},
                {"$set": {"manual": manual_data.manual}}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Manual saved successfully"}
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.get("/tasks/manual")
async def get_manual(
    task_id: str,
    current_user: dict = Depends(oauth2_scheme),
):
    """Get the manual for a specific task.

    Args:
        task_id (str): The ID of the task to retrieve the manual for.
        current_user (dict): The current authenticated user.

    Returns:
        JSONResponse: A response containing the manual.

    Raises:
        HTTPException: If the user is not authorized or an error occurs.
    """
    try:
        # Check if the current user is an admin
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You do not have permission to perform this action."
            )

        # Retrieve the manual for the specified task
        task_manual = await tasks_collection.find_one(
            {"_id": task_id},
            {"_id": 0, "manual": 1}
        )

        manual = {}
        if task_manual:
            manual["task_manual"] = task_manual["manual"]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=manual
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.get("/user/tasks")
async def get_tasks_by_user(
    current_user: dict = Depends(oauth2_scheme),
):
    """Get all tasks assigned to the current user.

    Args:
        current_user (dict): The current authenticated user.

    Returns:
        JSONResponse: A response containing the list of tasks.

    Raises:
        HTTPException: If an error occurs.
    """
    try:
        # Get user's email from the token
        user_email = current_user["email"]

        # Retrieve all tasks assigned to the user
        tasks = await tasks_collection.find(
            {"assignee": user_email},
            {
                "_id": 1,
                "text": 1,
                "task_description": 1,
                "start": 1,
                "end": 1,
                "parent": 1,
                "assignee": 1,
                "progress": 1,
                "created_at": 1,
                "created_by": 1,
                "type": 1,
                "classification": 1,
                "open": 1
            }
        ).to_list(length=None)

        # Convert datetime objects to date strings
        for task in tasks:
            if "created_at" in task and "start" in task and "end" in task:
                task["start"] = task["start"].date().isoformat()
                task["end"] = task["end"].date().isoformat()
                task["created_at"] = task["created_at"].date().isoformat()
                task["id"] = task["_id"]
                del task["_id"]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"tasks": tasks}
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.get("/user/tasks/details")
async def get_task_details(
    task_id: str,
    current_user: dict = Depends(oauth2_scheme),
):
    """Get detailed information about a specific task.

    Args:
        task_id (str): The ID of the task to retrieve details for.
        current_user (dict): The current authenticated user.

    Returns:
        JSONResponse: A response containing the task details.

    Raises:
        HTTPException: If the task is not found or an error occurs.
    """
    try:
        # Get user's email from the token
        user_email = current_user["email"]

        # Find the task
        task = await tasks_collection.find_one(
            {"_id": task_id},
            {
                "_id": 1,
                "text": 1,
                "task_id": 1,
                "task_description": 1,
                "start": 1,
                "end": 1,
                "parent": 1,
                "assignee": 1,
                "progress": 1,
                "created_at": 1,
                "created_by": 1,
                "type": 1,
                "classification": 1,
                "open": 1,
                "status": 1,
                "manual": 1
            }
        )

        # Convert datetime objects to date strings
        if "created_at" in task and "start" in task and "end" in task:
            task["start"] = task["start"].date().isoformat()
            task["end"] = task["end"].date().isoformat()
            task["created_at"] = task["created_at"].date().isoformat()
            task["id"] = task["_id"]
            del task["_id"]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"task": task}
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.put("/tasks/update-status")
async def update_task_status(
    task_data: UpdateTaskStatusModel,
    current_user: dict = Depends(oauth2_scheme),
):
    """Update task status and progress.

    Args:
        task_data (UpdateTaskStatusModel): The task status update data.
        current_user (dict): The current authenticated user.

    Returns:
        JSONResponse: A response indicating the update status.

    Raises:
        HTTPException: If the task is not found, the user is not authorized, or an error occurs.
    """
    try:
        # Get user's email from the token
        user_email = current_user["email"]

        # Find the task
        task = await tasks_collection.find_one({"_id": task_data.task_id})

        # Check if the task is assigned to the current user
        if task["assignee"] != user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this task."
            )

        # Update task status and progress
        update_data = {
            "status": task_data.status,
            "progress": task_data.progress,
            "updated_at": datetime.now(),
            "updated_by": user_email,
        }

        if task_data.status == "completed" or task_data.progress == 100:
            update_data["type"] = "completed"
            update_data["end"] = datetime.now()
            if datetime.now() > task["base_end"]:
                update_data["type"] = "exceeded"

        await tasks_collection.update_one(
            {"_id": task_data.task_id},
            {"$set": update_data}
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Task status updated successfully"}
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.get("/tasks/linked")
async def get_linked_tasks(
    task_id: str,
    current_user: dict = Depends(oauth2_scheme),
):
    """Get all tasks that are linked to the specified task.

    Args:
        task_id (str): The ID of the task to find linked tasks for.
        current_user (dict): The current authenticated user.

    Returns:
        JSONResponse: A response containing the linked tasks.

    Raises:
        HTTPException: If an error occurs.
    """
    try:
        # Get user's email from the token
        user_email = current_user["email"]

        # Find all links where this task is the target
        links_doc = await links_collection.find_one({})
        if not links_doc or "links" not in links_doc:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"linked_tasks": []}
            )

        # Get all source task IDs where this task is the target
        source_task_ids = [
            link["source"]
            for link in links_doc["links"]
            if link["target"] == task_id
        ]

        if not source_task_ids:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"linked_tasks": []}
            )

        # Get the task details for all source tasks
        linked_tasks = await tasks_collection.find(
            {"_id": {"$in": source_task_ids}},
            {
                "_id": 1,
                "text": 1,
                "task_id": 1,
                "status": 1,
                "progress": 1
            }
        ).to_list(length=None)

        # Convert _id to id for consistency
        for task in linked_tasks:
            task["id"] = task["_id"]
            del task["_id"]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"linked_tasks": linked_tasks}
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.post("/tasks/report")
async def create_or_update_report(
    report_data: ReportInputDataModel,
    current_user: dict = Depends(oauth2_scheme),
):
    """Create or update a report for a specific task.

    Args:
        report_data (ReportInputDataModel): The report data.
        current_user (dict): The current authenticated user.

    Returns:
        JSONResponse: A response indicating the update status.

    Raises:
        HTTPException: If the user is not authorized or an error occurs.
    """
    try:
        # Check if the current user is a user (not admin)
        if current_user["role"] not in ["user", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action."
            )

        # Check if a report for the task already exists
        task_exists = await tasks_collection.find_one({"_id": report_data.id})

        if task_exists:
            # Update the existing report
            await tasks_collection.update_one(
                {"_id": report_data.id},
                {"$set": {"report": report_data.report}}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Report saved successfully"}
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.get("/tasks/report")
async def get_report(
    task_id: str,
    current_user: dict = Depends(oauth2_scheme),
):
    """Get the report for a specific task.

    Args:
        task_id (str): The ID of the task to retrieve the report for.
        current_user (dict): The current authenticated user.

    Returns:
        JSONResponse: A response containing the report.

    Raises:
        HTTPException: If the user is not authorized or an error occurs.
    """
    try:
        # Check if the current user is a user (not admin)
        if current_user and current_user["role"] not in ["user", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You do not have permission to perform this action."
            )

        # Retrieve the report for the specified task
        report = await tasks_collection.find_one(
            {"_id": task_id},
            {
                "_id": 0,
                "report": 1,
                "text": 1,
                "progress": 1,
                "status": 1,
                "assignee": 1,
                "created_at": 1,
                "updated_at": 1,
                "start": 1,
                "end": 1
            }
        )

        if report:
            report["created_at"] = report["created_at"].isoformat()
            report["updated_at"] = report["updated_at"].isoformat()
            report["start"] = report["start"].isoformat()
            report["end"] = report["end"].isoformat()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=report
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.put("/tasks")
async def update_task(
    task_data: UpdateTaskModel,
    current_user: dict = Depends(oauth2_scheme),
):
    """Update a task.

    Args:
        task_data (UpdateTaskModel): The updated task data containing only the fields to update.
        current_user (dict): The current authenticated user.

    Returns:
        JSONResponse: A response indicating the update status.

    Raises:
        HTTPException: If the user is not authorized or an error occurs.
    """
    try:
        # Check if the current user is a user (not admin)
        if current_user and current_user["role"] not in ["user", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You do not have permission to perform this action."
            )

        # Handle task updates if task data is provided
        if task_data.task:
            # Convert task data to dict and remove None values
            task_update_data = {
                k: v for k, v in task_data.task.model_dump().items() if v is not None}

            # If there are fields to update
            if task_update_data:
                # Handle datetime fields
                if "start" in task_update_data:
                    task_update_data["start"] = datetime.combine(
                        task_update_data["start"], datetime.min.time())
                if "end" in task_update_data:
                    task_update_data["end"] = datetime.combine(
                        task_update_data["end"], datetime.max.time())

                # Update the task
                await tasks_collection.update_one(
                    {"_id": task_data.task_id},
                    {"$set": task_update_data}
                )

        # Handle links updates if links data is provided
        if task_data.links and task_data.project_id:
            links = []
            for link in task_data.links:
                links.append({
                    "link_id": str(uuid.uuid4()),
                    "source": link["source"],
                    "target": link["target"],
                    "type": link["type"]
                })

            # Check if links document exists for the project
            existing_links = await links_collection.find_one({"project_id": task_data.project_id})

            if existing_links:
                # Update existing links
                await links_collection.update_one(
                    {"project_id": task_data.project_id},
                    {"$set": {"links": links}}
                )
            else:
                # Create new links document
                await links_collection.insert_one({
                    "project_id": task_data.project_id,
                    "links": links,
                    "_id": str(uuid.uuid4())
                })

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Task updated successfully"}
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e
