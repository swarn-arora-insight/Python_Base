from fastapi import Depends
from src.IBusiness.IUserBusiness import IUserBusiness
from src.Business.UserBusiness import UserBusiness
def get_user_repo() -> IUserBusiness:
    return IUserBusiness()

def get_user_service(user_repo=Depends(get_user_repo)) -> UserBusiness:
    return UserBusiness(user_repo=user_repo)