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
import aiohttp
import aiofiles

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

# Add these constants near the top with other imports
UPLOAD_DIR = Path("/tmp/cameo_uploads")
ASSETS_DIR = Path("rpi_control/assets/camouflage")
BACKEND_URL = "https://api.cameo-ai.com/generate-pattern"  # Placeholder URL

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


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

    Workflow:
    1. Save uploaded file locally
    2. Send to backend server for processing
    3. Save returned camouflage pattern
    4. Return success response

    Args:
        file (UploadFile): The image file to process

    Returns:
        dict: Information about the processed file and generated pattern

    Raises:
        HTTPException: If there's an error in processing
    """
    try:
        # Generate unique filename for upload
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{file.filename.split('.')[0]}_{os.urandom(4).hex()}{file_extension}"
        upload_path = UPLOAD_DIR / unique_filename

        # Save uploaded file
        contents = await file.read()
        async with aiofiles.open(upload_path, "wb") as f:
            await f.write(contents)

        # Prepare file for sending to backend
        form_data = aiohttp.FormData()
        form_data.add_field('file',
                            open(upload_path, 'rb'),
                            filename=unique_filename,
                            content_type=file.content_type)

        # Send to backend server
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(BACKEND_URL, data=form_data) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Backend server error: {await response.text()}"
                        )

                    # Save the returned camouflage pattern
                    pattern_data = await response.read()
                    pattern_path = ASSETS_DIR / "current.png"
                    async with aiofiles.open(pattern_path, "wb") as f:
                        await f.write(pattern_data)

            except aiohttp.ClientError as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Error communicating with backend server: {str(e)}"
                )

        return {
            "status": "success",
            "original_filename": file.filename,
            "saved_as": unique_filename,
            "pattern_path": str(pattern_path),
            "size": len(contents)
        }

    except Exception as e:
        # Clean up uploaded file if it exists
        if 'upload_path' in locals() and upload_path.exists():
            upload_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("rpi_control.api.main:app",
                host="0.0.0.0", port=8000, reload=True)
