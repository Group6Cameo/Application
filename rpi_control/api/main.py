"""
This module serves as the main FastAPI application entry point, defining all routes
and their handlers. It implements a REST API for managing VastAI instance management
and image processing for camouflage generation.

The API provides endpoints for:
- Health checking (/)
- Image processing for camouflage generation (/process-image)

Environment Variables Required:
    - VAST_AI_API_KEY: Authentication key for VastAI service

Technical Details:
    - Supports image uploads up to 3MB
    - Accepts JPG and PNG formats
    - Implements automatic cleanup of temporary files
    - Uses async/await for efficient I/O operations
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
from rpi_control.api.services.vast_ai_service import VastAIService
from rpi_control.utils.url_store import save_backend_url, get_backend_url, clean_backend_url

# Initialize FastAPI app and VastAI service
app = FastAPI(
    title="Cameo API",
    description="API for managing Cameo's camouflage model",
    version="1.0.0"
)

# Clean up any existing backend URL

# Add VastAI service initialization
vast_service = VastAIService()

# Global variable for backend URL
BACKEND_URL = None


@app.on_event("startup")
async def startup_event():
    """Initialize VastAI instance and set backend URL on startup"""
    global BACKEND_URL
    clean_backend_url()
    # result = await vast_service.create_instance()
    # if result["status"] != "success":
    #     raise RuntimeError(
    #         f"Failed to create VastAI instance: {result['message']}")

    # # Extract IP and port from the response
    # instance_ip = result["public_ip"][0]
    # instance_port = result["port"]
    BACKEND_URL = f"http://195.0.159.206:23742"

    # Save the backend URL
    save_backend_url(BACKEND_URL)
    print(f"Backend URL set to: {BACKEND_URL}")

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

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/", tags=["health"])
async def root():
    """
    Health check endpoint to verify API availability.

    Returns:
        dict: Simple welcome message indicating API is operational
    """
    return {"message": "Welcome to Cameo API"}


@app.post("/process-image", tags=["ml"])
async def process_image(
    file: UploadFile = File(...),
):
    """
    Process an uploaded image file through the ML model to generate a camouflage pattern.

    This endpoint handles the complete flow of:
    1. Image upload validation and saving
    2. Communication with the ML backend server
    3. Saving the generated camouflage pattern
    4. Cleanup of temporary files

    Args:
        file (UploadFile): The image file to process. Must be JPG or PNG format, max 3MB.

    Returns:
        dict: A dictionary containing:
            - status: "success" if processing completed
            - original_filename: Name of the uploaded file
            - saved_as: Unique filename generated for the upload
            - pattern_path: Path where the generated pattern was saved
            - size: Size of the uploaded file in bytes

    Raises:
        HTTPException:
            - 400: Invalid file type or size
            - 500: Server-side processing error
            - 503: Backend communication error
            - 504: Backend timeout
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
            if len(contents) > 10 * 1024 * 1024:  # 10MB limit
                raise HTTPException(
                    status_code=400,
                    detail="File size too large. Maximum size is 10MB"
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
                async with session.get(f"http://195.0.159.206:23742/generate-camouflage", data=form_data, timeout=60) as response:
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
