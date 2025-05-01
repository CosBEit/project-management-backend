from pydantic import BaseModel, EmailStr

class AddUserInputDataModel(BaseModel):
    email: EmailStr
    role: str

class RegisterUserInputDataModel(BaseModel):
    email: EmailStr
    password: str
    token: str
