# Business Logic Functions
from src.Model.OperationResult import OperationResult
from src.Model.UserModel import users, User
from src.IBusiness.IUserBusiness import *

class UserBusiness(IUserBusiness):

    def __init__(self, user_repo: IUserBusiness):
        self.user_repo = user_repo

    def register_user(username: str, email: str) -> OperationResult:
        if username in users:
            return OperationResult(success=False, message="User already exists.", status_code=409)

        new_user = {"username": username, "email": email}
        users[username] = new_user
        return OperationResult(data=new_user, message="User registered successfully.", status_code=201)

    def get_user(username: str) -> OperationResult:
        user = users.get(username)
        if user is None:
            return OperationResult(success=False, message="User not found.", status_code=404)
        return OperationResult(data=user, message="User retrieved successfully.")
    
    def get_user2(username: str) -> OperationResult:
        user = users.get(username)
        if user is None:
            return OperationResult(success=False, message="User not found.", status_code=404)
        return OperationResult(data=user, message="User retrieved successfully.")