"""
This module serves as the main FastAPI application entry point, defining all routes
and their handlers. It implements a REST API for managing VastAI instance management.

Environment Variables Required:
    - VAST_AI_API_KEY: Authentication key for VastAI service
"""

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from rpi_control.api.routers import server
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Cameo API",
    description="API for managing Cameo's camouflage model",
    version="1.0.0"
)

# Configure CORS to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(server.router)


@app.get("/", tags=["health"])
async def root():
    """Health check endpoint. Does not require authentication."""
    return {"message": "Welcome to Cameo API"}


@app.post("/process-image", tags=["ml"])
async def process_image(
    file: UploadFile = File(...)
):
    """Process an uploaded image file through the ML model."""
    return {"filename": file.filename}

if __name__ == "__main__":
    uvicorn.run("rpi_control.api.main:app",
                host="0.0.0.0", port=8000, reload=True)
