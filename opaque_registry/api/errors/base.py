from typing import Any

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder


class ApiException(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: str,
        details: dict = {},
        headers: dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=status_code,
            detail=jsonable_encoder(
                {"error": type(self).__name__, "message": message, **details}
            ),
            headers=headers,
        )
