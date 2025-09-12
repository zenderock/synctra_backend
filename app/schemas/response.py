from pydantic import BaseModel
from typing import Any, Optional, Generic, TypeVar

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    status: str
    message: str
    data: Optional[T] = None
    
    @classmethod
    def success(cls, data: T = None, message: str = "Succès"):
        return cls(status="success", message=message, data=data)
    
    @classmethod
    def error(cls, message: str, data: Any = None, status_code: int = 400):
        from fastapi import HTTPException
        raise HTTPException(status_code=status_code, detail={
            "status": "error",
            "message": message,
            "data": data
        })

class ProjectListResponse(ApiResponse):
    pass

class ProjectDetailResponse(ApiResponse):
    pass
