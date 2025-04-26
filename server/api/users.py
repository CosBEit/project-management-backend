# import uuid
# from datetime import datetime, timedelta
import traceback
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from server.dependencies.auth import OAuth2PasswordBearerWithCookie
# from app.schema.auth_schema import AddUserInputDataModel
from server.configs.db import users_collection

# from app.dependencies.email import send_invitation_email

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/auth/login")
router = APIRouter()


# @router.post("/auth/admin/add/user")
# async def add_user(add_user_data: AddUserInputDataModel, current_user: str = Depends(oauth2_scheme)):
#     """Add a new user to the database.

#     Args:
#         add_user_data (AddUserInputDataModel): The user's data including email and role.
#         current_user (str): The current authenticated user.

#     Returns:
#         JSONResponse: A response indicating the addition status.

#     Raises:
#         HTTPException: If the user is not authorized or an error occurs during the process.
#     """
#     try:
#         # Get the current user's role from the request
#         if current_user["role"] != "admin":
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="You do not have permission to perform this action.",
#             )

#         # Check if the user already exists
#         existing_user = await get_user(add_user_data.email)
#         if existing_user:
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail="Email address already exists.",
#             )

#         link_expiration = 1  # 1 day
#         # Add the new user to the database
#         new_user = {
#             "_id": str(uuid.uuid4()),
#             "email": add_user_data.email,
#             "role": add_user_data.role,
#             "created_at": datetime.now(),
#             "status": "pending",
#         }
#         link_expiration = {"format": "days", "value": 1}  # 30 minutes

#         # Create a unique token
#         token = create_csrf_token(
#             data={
#                 "_id": new_user["_id"],
#                 "email": add_user_data.email,
#                 "role": add_user_data.role
#             },
#             secret_key=settings.csrf_token_secrete_key,
#             expires_delta=timedelta(
#                 **{link_expiration["format"]: link_expiration["value"]}),
#         )

#         # Construct the setup link with the bearer token
#         frontend_url = f"{settings.frontend_url}/create-account"
#         setup_link = f"{frontend_url}?token={token}"

#         # Send an email to the new user to set up their password
#         await send_invitation_email(add_user_data.email, setup_link, link_expiration)
#         await user_collection.insert_one(new_user)
#         content = {
#             "message": "User added successfully and email sent to set up password."
#         }
#         users = await user_collection.find({}, {"email": 1, "role": 1, "status": 1, "created_at": 1}).to_list(length=None)
#         for user in users:
#             if "created_at" in user:
#                 user["created_at"] = user["created_at"].date().isoformat()
#         content["users"] = users
#         return JSONResponse(status_code=status.HTTP_201_CREATED, content=content)

#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         traceback.print_exc()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
#         ) from e


# @router.get("/auth/users")
# async def get_all_users(current_user: str = Depends(oauth2_scheme)):
#     """Get all users' email, role, and status.

#     Args:
#         current_user (str): The current authenticated user.

#     Returns:
#         JSONResponse: A response containing the list of users.

#     Raises:
#         HTTPException: If the user is not authorized.
#     """
#     try:
#         # Check if the current user is an admin
#         if current_user["role"] != "admin":
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="You do not have permission to perform this action.",
#             )

#         # Retrieve all users from the database
#         users = await user_collection.find({}, {"email": 1, "role": 1, "status": 1, "created_at": 1}).to_list(length=None)

#         # Convert datetime objects to date strings
#         for user in users:
#             if "created_at" in user:
#                 user["created_at"] = user["created_at"].date().isoformat()

#         content = {"users": users}
#         print(user)
#         return JSONResponse(status_code=status.HTTP_200_OK, content=content)

#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         traceback.print_exc()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
#         ) from e


@router.get("/users/active")
async def get_active_users(current_user: str = Depends(oauth2_scheme)):
    """Get all active users' id and email.

    Args:
        current_user (str): The current authenticated user.

    Returns:
        JSONResponse: A response containing the list of active users.

    Raises:
        HTTPException: If the user is not authorized.
    """
    try:
        # Check if the current user is an admin
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You do not have permission to perform this action.",
            )

        # Retrieve all active users from the database
        active_users = await users_collection.find(
            {"status": "active"}, 
            {"_id": 1, "email": 1}).to_list(length=None)

        content = {"active_users": active_users}
        return JSONResponse(status_code=status.HTTP_200_OK, content=content)

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


# @router.put("/auth/users/{user_id}")
# async def update_user(user_id: str, user_data: dict, current_user: str = Depends(oauth2_scheme)):
#     """Update a user's email and role.

#     Args:
#         user_id (str): The ID of the user to update.
#         user_data (dict): The updated user data including email and role.
#         current_user (str): The current authenticated user.

#     Returns:
#         JSONResponse: A response containing the updated user data.

#     Raises:
#         HTTPException: If the user is not authorized or an error occurs during the process.
#     """
#     try:
#         # Check if the current user is an admin
#         if current_user["role"] != "admin":
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="You do not have permission to perform this action.",
#             )

#         # Find the existing user
#         existing_user = await user_collection.find_one({"_id": user_id})
#         if not existing_user:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="User not found.",
#             )

#         # Check if email is being changed and if it already exists
#         if user_data["email"] != existing_user["email"]:
#             email_exists = await user_collection.find_one({"email": user_data["email"], "_id": {"$ne": user_id}})
#             if email_exists:
#                 raise HTTPException(
#                     status_code=status.HTTP_409_CONFLICT,
#                     detail="Email address already exists.",
#                 )

#         # Prepare update data
#         update_data = {
#             "email": user_data["email"],
#             "role": user_data["role"],
#             "updated_at": datetime.now(),
#             "updated_by": current_user["email"]
#         }

#         # Update the user
#         await user_collection.update_one(
#             {"_id": user_id},
#             {"$set": update_data}
#         )

#         # Get the updated user
#         updated_user = await user_collection.find_one(
#             {"_id": user_id},
#             {"_id": 1, "email": 1, "role": 1, "status": 1, "created_at": 1}
#         )

#         # Format dates for response
#         if "created_at" in updated_user:
#             updated_user["created_at"] = updated_user["created_at"].date(
#             ).isoformat()

#         return JSONResponse(
#             status_code=status.HTTP_200_OK,
#             content={
#                 "message": "User updated successfully",
#                 "user": updated_user
#             }
#         )

#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         traceback.print_exc()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=str(e)
#         ) from e


# @router.delete("/auth/users/{user_id}")
# async def delete_user(user_id: str, current_user: str = Depends(oauth2_scheme)):
#     """Delete a user from the database.

#     Args:
#         user_id (str): The ID of the user to delete.
#         current_user (str): The current authenticated user.

#     Returns:
#         JSONResponse: A response indicating the deletion status.

#     Raises:
#         HTTPException: If the user is not authorized or an error occurs during the process.
#     """
#     try:
#         # Check if the current user is an admin
#         if current_user["role"] != "admin":
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="You do not have permission to perform this action.",
#             )

#         # Find the existing user
#         existing_user = await user_collection.find_one({"_id": user_id})
#         if not existing_user:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="User not found.",
#             )

#         # Prevent deleting yourself
#         if existing_user["_id"] == current_user["_id"]:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="You cannot delete your own account.",
#             )

#         # Delete the user
#         await user_collection.delete_one({"_id": user_id})

#         return JSONResponse(
#             status_code=status.HTTP_200_OK,
#             content={
#                 "message": "User deleted successfully"
#             }
#         )

#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         traceback.print_exc()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=str(e)
#         ) from e
