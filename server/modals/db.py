import os
import traceback
from typing import Optional

import motor.motor_asyncio
from fastapi import HTTPException 
from dotenv import load_dotenv

load_dotenv()


class ConnectMongoDB:

    @staticmethod
    def get_connection():
        try:
            mongo_url = os.getenv('db_url')
            return motor.motor_asyncio.AsyncIOMotorClient(mongo_url)

        except Exception as e:
            traceback.print_exc()
            status_code, detail = e.args
        raise HTTPException(status_code=status_code, detail=str(detail))
