"""
API package initialization.

This module sets up the API framework for the gesture-voice control system.
It handles API initialization, configuration, and provides the main router.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create the FastAPI application
app = FastAPI(
    title="Gesture Voice Control API",
    description="API for controlling system via gestures and voice commands",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers from route modules
from api.routes import auth, voice, gestures, system

# Include all route modules
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(voice.router, prefix="/voice", tags=["Voice Commands"])
app.include_router(gestures.router, prefix="/gestures", tags=["Gesture Controls"])
app.include_router(system.router, prefix="/system", tags=["System Controls"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "Gesture Voice Control API",
        "version": "0.1.0",
        "status": "running"
    }