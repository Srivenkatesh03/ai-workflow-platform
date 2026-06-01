from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


def api_error(message: str, status_code: int = 400, errors: list[dict] | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "message": message, "errors": errors or []},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return api_error(str(exc.detail), exc.status_code)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        if app.debug:
            return api_error(str(exc), 500)
        return api_error("Internal server error", 500)

