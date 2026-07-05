from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from config import settings
from models.request import AgentRequest
from models.response import AgentResponse
from agent.workflow import run_agent

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
)


@app.get("/")
async def root():
    return {
        "message": "Autonomous Agent API",
        "version": settings.app_version,
        "endpoints": {
            "GET /": "This info",
            "GET /health": "Health check",
            "POST /agent": "Run the autonomous agent with a request",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/agent", response_model=AgentResponse)
async def agent_endpoint(request: AgentRequest):
    if not request.request.strip():
        raise HTTPException(status_code=400, detail="Request cannot be empty.")

    try:
        result = run_agent(request.request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}",
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )
