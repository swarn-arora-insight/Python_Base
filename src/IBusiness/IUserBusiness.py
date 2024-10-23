from abc import ABC, abstractmethod
from src.Model.OperationResult import OperationResult

# creating interface
class IUserBusiness(ABC):
   @abstractmethod
   def register_user(username: str, email: str) -> OperationResult:
      raise NotImplementedError("Please Implement this method")

   @abstractmethod
   def get_user(username: str) -> OperationResult:
      raise NotImplementedError("Please Implement this method")
   

#    # creating interface
# class UserBusiness(IUserBusiness):
#    def register_user(username: str, email: str) -> OperationResult:
#       raise NotImplementedError("Please Implement this method")

#    def get_user(username: str) -> OperationResult:
#       raise NotImplementedError("Please Implement this method")