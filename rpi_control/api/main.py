"""
This module serves as the main FastAPI application entry point, defining all routes
and their handlers. It implements a REST API for managing VastAI instance management.

Environment Variables Required:
    - VAST_AI_API_KEY: Authentication key for VastAI service
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from pathlib import Path
import aiohttp
import aiofiles
import asyncio

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

# Add these constants near the top with other imports
UPLOAD_DIR = Path("/tmp/cameo_uploads")
ASSETS_DIR = Path("rpi_control/assets/camouflage")
BACKEND_URL = "http://213.5.130.78:17033/generate-camouflage"  # Placeholder URL

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/", tags=["health"])
async def root():
    """Health check endpoint. Does not require authentication."""
    return {"message": "Welcome to Cameo API"}


@app.post("/process-image", tags=["ml"])
async def process_image(
    file: UploadFile = File(...),
):
    """
    Process an uploaded image file through the ML model.
    """
    if not file:
        raise HTTPException(
            status_code=400,
            detail="No file uploaded"
        )

    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )

    try:
        # Generate unique filename for upload
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ['.jpg', '.jpeg', '.png']:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload JPG, PNG, or GIF"
            )

        unique_filename = f"{file.filename.split('.')[0]}_{os.urandom(4).hex()}{file_extension}"
        upload_path = UPLOAD_DIR / unique_filename

        # Save uploaded file
        try:
            contents = await file.read()
            if len(contents) > 3 * 1024 * 1024:  # 3MB limit
                raise HTTPException(
                    status_code=400,
                    detail="File size too large. Maximum size is 3MB"
                )

            async with aiofiles.open(upload_path, "wb") as f:
                await f.write(contents)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save uploaded file: {str(e)}"
            )

        # Prepare file for sending to backend
        try:
            form_data = aiohttp.FormData()
            form_data.add_field('image',
                                open(upload_path, 'rb'),
                                filename=unique_filename,
                                content_type=file.content_type)

            async with aiohttp.ClientSession() as session:
                async with session.get(BACKEND_URL, data=form_data, timeout=60) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Backend server error: {await response.text()}"
                        )

                    # Save the returned camouflage pattern
                    pattern_data = await response.read()
                    if not pattern_data:
                        raise HTTPException(
                            status_code=500,
                            detail="Backend returned empty response"
                        )

                    pattern_path = ASSETS_DIR / f"pattern_{unique_filename}"
                    async with aiofiles.open(pattern_path, "wb") as f:
                        await f.write(pattern_data)

        except aiohttp.ClientError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Error communicating with backend server: {str(e)}"
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail="Backend server timeout"
            )

        return {
            "status": "success",
            "original_filename": file.filename,
            "saved_as": unique_filename,
            "pattern_path": str(pattern_path),
            "size": len(contents)
        }

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is

    except Exception as e:
        # Log the error here (you should add proper logging)
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the image"
        )

    finally:
        # Clean up uploaded file if it exists
        if 'upload_path' in locals() and upload_path.exists():
            try:
                upload_path.unlink()
            except Exception as e:
                print(f"Failed to clean up temporary file: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("rpi_control.api.main:app",
                host="0.0.0.0", port=8000, reload=True)
