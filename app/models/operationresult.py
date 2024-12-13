from typing import Generic, TypeVar, List, Optional, Iterable
from http import HTTPStatus
from enum import Enum

T = TypeVar("T")


class OperationResultType(Enum):
    SUCCESS = 0
    ERROR = 1


class MessageType(Enum):
    SUCCESS_MESSAGE = "SuccessMessage"
    ERROR_MESSAGE = "ErrorMessage"


class OperationResult(Generic[T]):
    def __init__(self, 
                 data_object: Optional[T] = None,
                 message_type: Optional[MessageType] = None, 
                 messages: Optional[Iterable[str]] = None,
                 errors: Optional[Iterable[str]] = None, 
                 http_status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR):
        self.data_object = data_object
        self.http_status = http_status

        if data_object is not None:
            self._operation_result_value = OperationResultType.SUCCESS
            self.success_messages = messages if message_type == MessageType.SUCCESS_MESSAGE else []
            self.errors = []
        elif errors is not None:
            self._operation_result_value = OperationResultType.ERROR
            self.errors = list(errors)
        else:
            self._operation_result_value = OperationResultType.ERROR
            self.errors = ["Null Data Object!"]
        
        self.success_messages = messages if message_type == MessageType.SUCCESS_MESSAGE else []

    @property
    def succeeded(self) -> bool:
        return self._operation_result_value == OperationResultType.SUCCESS

    @staticmethod
    def success_without_data() -> 'OperationResult[T]':
        return OperationResult(None)

    @staticmethod
    def failed(http_status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR, *errors: str) -> 'OperationResult[T]':
        return OperationResult(errors=errors, http_status=http_status)


class RootObject(Generic[T]):
    def __init__(self, error: bool, data: T):
        self.error = error
        self.data = data


class SubRootObject(Generic[T]):
    def __init__(self, items: List[T]):
        self.items = items


class SubRootObjectWithTotalCount(Generic[T]):
    def __init__(self, total_count: int, items: List[T]):
        self.total_count = total_count
        self.items = items


class ClsError:
    def __init__(self):
        self.message = ""
        self.errors: List[str] = []