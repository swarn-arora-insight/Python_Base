from pydantic import BaseModel

users = {}

# User model for request validation
class User(BaseModel):
    username: str
    email: str