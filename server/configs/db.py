import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

client = AsyncIOMotorClient(os.getenv('db_url'))
database = client[os.getenv('db_name')]
users_collection = database["users"]
projects_collection = database["projects"]
tasks_collection = database["tasks"]
links_collection = database["links"]
