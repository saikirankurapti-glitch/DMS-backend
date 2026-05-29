"""
FastAPI Application Entry Point
Pharma Document Management System (DMS)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1 import api_router

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    Pharma Document Management System (DMS) with controlled SOP lifecycle 
    and role-based access control.
    
    **Phase 1: User Management and RBAC**
    
    ## Features
    - User authentication with JWT tokens
    - Role-based access control (Author, Reviewer, Approver, DMS_Admin)
    - Complete user lifecycle management (CRUD)
    - Admin-only password reset
    - Comprehensive audit logging for compliance
    - FDA 21 CFR Part 11 ready
    
    ## Roles
    - **Author**: Create and edit documents
    - **Reviewer**: Review and comment on documents
    - **Approver**: Approve or reject documents with e-signature
    - **DMS_Admin**: Full system administration including user management
    """,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def root():
    """Root endpoint - API health check"""
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)


