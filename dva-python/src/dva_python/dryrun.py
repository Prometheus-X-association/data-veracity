from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from .log import get_logger
from .processing import AoVRequest, handle_aov_request


logger = get_logger()
app = FastAPI()


@app.post("/")
def process_request(req: AoVRequest):
    logger.info("Received AoV request", request=req)
    aov_gen_req = handle_aov_request(req)
    logger.info(f"Would be sending request: {str(aov_gen_req)}")
    return JSONResponse(aov_gen_req.model_dump())


@app.exception_handler(RequestValidationError)
def handle_validation_exception(request: AoVRequest, err: RequestValidationError):
    logger.error("Validation error during request processing", error=err)
    return Response(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
