from os import link
import uuid
import traceback
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from server.modals.tasks import (
    CreateTaskInputDataModel,
    UpdateTaskModel,
    CommentInputDataModel
)
from server.dependencies.auth import OAuth2PasswordBearerWithCookie
from server.configs.db import tasks_collection, links_collection, projects_collection
from server.dependencies.send_emails import send_task_creation_email, send_assignee_change_email, send_task_start_email, send_task_completion_email

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

        # Parse the date strings into datetime objects
        start_date = datetime.strptime(task_data.start, "%Y-%m-%d").date()
        end_date = datetime.strptime(task_data.end, "%Y-%m-%d").date()

        new_task = {
            "_id": _id,
            "project_id": task_data.project_id,
            "text": task_data.text,
            "task_description": task_data.task_description,
            "start": datetime.combine(start_date, datetime.min.time()),
            "end": datetime.combine(end_date, datetime.max.time()),
            "base_start": datetime.combine(start_date, datetime.min.time()),
            "base_end": datetime.combine(end_date, datetime.max.time()),
            "assignee": task_data.assignee,
            "parent": task_data.parent,
            "progress": task_data.progress,
            "classification": task_data.classification,
            "type": task_data.type,
            "open": task_data.open,
            "created_at": datetime.now(),
            "status": "not_started",
            "created_by": current_user["email"],
            "priority": task_data.priority
        }

        await tasks_collection.insert_one(new_task)

        # Send email notification to the assignee if email is provided
        if task_data.assignee:
            try:
                await send_task_creation_email(task_data.assignee, new_task)
            except Exception as e:
                # Log the error but don't fail the task creation
                print(f"Failed to send task creation email: {str(e)}")

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
    project_id: str = None,
    email: str = None,
    current_user: dict = Depends(oauth2_scheme),
):
    """Get all tasks for a specific project or user.

    Args:
        project_id (str, optional): The ID of the project to retrieve tasks for.
        email (str, optional): The email of the user to retrieve tasks for.
        current_user (dict): The current authenticated user.

    Returns:
        dict: A dictionary containing the list of tasks and project name.

    Raises:
        HTTPException: If the user is not authorized or an error occurs.
    """
    try:
        # Build the query based on provided parameters
        query = {}
        # Build the query based on provided parameters
        query = {}
        if project_id:
            query["project_id"] = project_id
        if email:
            query["assignee"] = email

        # Get project details if project_id is provided
        project_name = "All Projects"
        if project_id:
            project = await projects_collection.find_one(
                {"_id": project_id},
                {"project_name": 1}
            )
            if project:
                project_name = project.get("project_name", "Unknown Project")

        # Retrieve all tasks matching the query
        tasks = await tasks_collection.find(
            query,
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
                "open": 1,
                "project_id": 1
            }
        ).to_list(length=None)

        # Convert datetime objects to date strings
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

        # Get project names for each task
        for task in tasks:
            if "project_id" in task:
                project = await projects_collection.find_one(
                    {"_id": task["project_id"]},
                    {"project_name": 1}
                )
                if project:
                    task["project_name"] = project.get("project_name", "Unknown Project")

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


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    current_user: dict = Depends(oauth2_scheme),
):
    """Get a specific task by ID.

    Args:
        task_id (str): The ID of the task to retrieve.
        current_user (dict): The current authenticated user.
        db: Database connection.

    Returns:
        dict: The task details.

    Raises:
        HTTPException: If the task is not found or an error occurs.
    """
    try:
        task = await tasks_collection.find_one(
            {"_id": task_id},
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
                "status": 1,
                "open": 1,
                "priority": 1
            }
        )

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        # Convert datetime objects to date strings
        if "created_at" in task and "start" in task and "end" in task:
            task["start"] = task["start"].date().isoformat()
            task["end"] = task["end"].date().isoformat()
            task["created_at"] = task["created_at"].date().isoformat()

        task["id"] = task["_id"]
        del task["_id"]

        return task

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.get("/tasks/links/{project_id}")
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

        # First check if project exists
        project = await projects_collection.find_one({"_id": project_id})
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Retrieve the links
        links = await links_collection.find_one(
            {"project_id": project_id},
            {"_id": 1, "links": 1}
        )

        # If no links document exists or no links array, return empty array
        if not links or "links" not in links:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"links": []}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"links": links["links"]}
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

        # Get the current task data
        current_task = await tasks_collection.find_one({"_id": task_data.task_id})

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

                # Check if assignee is being changed
                if "assignee" in task_update_data and task_update_data["assignee"] != current_task["assignee"]:
                    # Send email to both old and new assignee
                    try:
                        # Send to old assignee
                        await send_assignee_change_email(
                            current_task["assignee"],
                            current_task,
                            current_task["assignee"],
                            task_update_data["assignee"]
                        )
                        # Send to new assignee
                        await send_assignee_change_email(
                            task_update_data["assignee"],
                            current_task,
                            current_task["assignee"],
                            task_update_data["assignee"]
                        )
                    except Exception as e:
                        # Log the error but don't fail the task update
                        print(
                            f"Failed to send assignee change emails: {str(e)}")

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
                    "id": str(uuid.uuid4()),
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


@router.post("/tasks/comment")
async def create_comment(
    comment_data: CommentInputDataModel,
    current_user: dict = Depends(oauth2_scheme),
):
    """Create a comment for a specific task.

    Args:
        comment_data (CommentInputDataModel): The comment data.
        current_user (dict): The current authenticated user.

    Returns:
        JSONResponse: A response indicating the comment creation status.

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

        # Create the comment object
        created_at = datetime.now()
        comment = {
            "id": str(uuid.uuid4()),
            "content": comment_data.content,
            "created_at": created_at.isoformat(),  # Convert datetime to ISO format string
            "created_by": current_user["email"]
        }

        # Add the comment to the task's comments array
        await tasks_collection.update_one(
            {"_id": comment_data.task_id},
            {"$push": {"comments": {
                "id": comment["id"],
                "content": comment["content"],
                "created_at": created_at,  # Store as datetime in database
                "created_by": comment["created_by"]
            }}}
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Comment added successfully", "comment": comment}
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.get("/tasks/comments/{task_id}")
async def get_comments(
    task_id: str,
    current_user: dict = Depends(oauth2_scheme),
):
    """Get all comments for a specific task.

    Args:
        task_id (str): The ID of the task to retrieve comments for.
        current_user (dict): The current authenticated user.

    Returns:
        JSONResponse: A response containing the comments.

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

        # Get the task with its comments
        task = await tasks_collection.find_one(
            {"_id": task_id},
            {"comments": 1}
        )

        comments = task.get("comments", []) if task else []

        # Convert datetime objects to ISO format strings
        for comment in comments:
            if "created_at" in comment:
                comment["created_at"] = comment["created_at"].isoformat()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"comments": comments}
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.delete("/tasks/{task_id}/{project_id}")
async def delete_task(
    task_id: str,
    project_id: str,
    current_user: dict = Depends(oauth2_scheme),
):
    """Delete a task and its associated links.

    Args:
        task_id (str): The ID of the task to delete.
        project_id (str): The ID of the project containing the task.
        current_user (dict): The current authenticated user.

    Returns:
        JSONResponse: A response indicating the deletion status.

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

        # Delete the task
        result = await tasks_collection.delete_one({"_id": task_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        # Get the current links document
        links_doc = await links_collection.find_one({"project_id": project_id})
        
        if links_doc and "links" in links_doc:
            # Filter out links that reference the deleted task
            updated_links = [
                link for link in links_doc["links"]
                if link["source"] != task_id and link["target"] != task_id
            ]
            
            # Update the links document
            await links_collection.update_one(
                {"project_id": project_id},
                {"$set": {"links": updated_links}}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Task and associated links deleted successfully"}
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.put("/tasks/update-status")
async def update_task_status(
    task_data: UpdateTaskModel,
    current_user: dict = Depends(oauth2_scheme),
):
    """Update task status and progress.

    Args:
        task_data (UpdateTaskModel): The task status update data.
        current_user (dict): The current authenticated user.

    Returns:
        JSONResponse: A response indicating the update status.

    Raises:
        HTTPException: If the task is not found or if an error occurs.
    """
    try:
        # Get user's email from the token
        user_email = current_user["email"]

        # Find the task
        task = await tasks_collection.find_one({"_id": task_data.task_id})

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found.",
            )

        # Check if the task is assigned to the current user
        if task["assignee"] != user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this task.",
            )

        # Update task status and progress
        update_data = {
            "status": task_data.task.status,
            "progress": task_data.task.progress,
            "updated_at": datetime.now(),
            "updated_by": user_email,
        }

        if task_data.task.status == "completed" or task_data.task.progress == 100:
            update_data["type"] = "completed"
            update_data["end"] = datetime.now()
            if datetime.now() > task["base_end"]:
                update_data["type"] = "exceeded"

        await tasks_collection.update_one(
            {"_id": task_data.task_id},
            {"$set": update_data}
        )

        print("task_data.task.status: ", task_data.task.status)
        print("task_data.task.progress: ", task_data.task.progress)

        # If task is started with 0 progress, send notification to creator
        if task_data.task.status == "started" and task_data.task.progress == 0:
            if task.get("created_by") and "@" in task["created_by"]:
                try:
                    # Prepare email data for task start notification
                    await send_task_start_email(task["created_by"], task)
                except Exception as e:
                    print(f"Failed to send task start notification email: {str(e)}")

        # If task is completed, send notifications
        if task_data.task.status == "completed":
            # Get all links where this task is the source
            links_doc = await links_collection.find_one({"project_id": task["project_id"]})
            if links_doc and "links" in links_doc:
                # Find all target tasks
                target_task_ids = [
                    link["target"]
                    for link in links_doc["links"]
                    if link["source"] == task_data.task_id
                ]

                if target_task_ids:
                    # Get details of all target tasks
                    target_tasks = await tasks_collection.find(
                        {"_id": {"$in": target_task_ids}},
                        {
                            "_id": 1,
                            "text": 1,
                            "task_description": 1,
                            "start": 1,
                            "end": 1,
                            "assignee": 1,
                            "classification": 1,
                            "created_by": 1
                        }
                    ).to_list(length=None)

                    # Send notifications to target task assignees
                    for target_task in target_tasks:
                        if target_task.get("assignee") and "@" in target_task["assignee"]:
                            try:
                                # Prepare email data for next task notification
                                await send_task_completion_email(target_task["assignee"], target_task, True)
                            except Exception as e:
                                print(f"Failed to send next task notification email: {str(e)}")

            # Send notification to task creator
            if task.get("created_by") and "@" in task["created_by"]:
                try:
                    # Prepare email data for task completion notification
                    await send_task_completion_email(
                        task["created_by"],
                        task,
                        False
                    )
                except Exception as e:
                    print(f"Failed to send task completion notification email: {str(e)}")

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
