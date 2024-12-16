"""
This module serves as the main FastAPI application entry point, defining all routes
and their handlers. It implements a REST API for managing VastAI instance management.

Environment Variables Required:
    - VAST_AI_API_KEY: Authentication key for VastAI service
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from rpi_control.api.routers import server
import uvicorn
import os
from pathlib import Path

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

# Mount static files directory
app.mount("/static", StaticFiles(directory="rpi_control/static"), name="static")

# Include routers
app.include_router(server.router)

# Add this constant near the top of the file
UPLOAD_DIR = Path("/tmp/cameo_uploads")

# Create upload directory if it doesn't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/", tags=["health"])
async def root():
    """Health check endpoint. Does not require authentication."""
    return {"message": "Welcome to Cameo API"}


@app.post("/process-image", tags=["ml"])
async def process_image(
    file: UploadFile = File(...)
):
    """
    Process an uploaded image file through the ML model.

    Args:
        file (UploadFile): The image file to process

    Returns:
        dict: Information about the processed file

    Raises:
        HTTPException: If there's an error saving the file
    """
    try:
        # Generate a unique filename to prevent overwrites
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{file.filename.split('.')[0]}_{os.urandom(4).hex()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        return {
            "filename": file.filename,
            "saved_as": unique_filename,
            "file_path": str(file_path),
            "size": len(contents)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving file: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("rpi_control.api.main:app",
                host="0.0.0.0", port=8000, reload=True)
