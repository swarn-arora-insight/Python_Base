class OperationResult:
    def __init__(self, data=None, success=True, message=None, status_code=200):
        self.data = data
        self.success = success
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        return {
            "data": self.data,
            "success": self.success,
            "message": self.message,
            "status_code": self.status_code,
        }