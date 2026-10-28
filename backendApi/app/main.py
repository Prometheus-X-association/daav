import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
import time
import logging.config

#Load settings
from app.config.settings import settings

#logging
from app.config.logging import setup_logging
logger = setup_logging(settings)

from app.config.database import db_config

from app.models.interface.dataset_interface import (
    Dataset, FileDataset, MongoDataset, MysqlDataset,
    ApiDataset, ElasticDataset, PTXDataset
)
from app.models.interface.workflow_interface import IProject
from app.models.interface.user_interface import User,PasswordResetToken
from app.models.interface.pdc_chain_interface import ServiceChainData

from app.services.migration_service import MigrationService
from app.services.reencryption_service import reencrypt_sensitive_fields
from app.config.secret_keys import log_temporary_secrets
from app.services.user_service import UserService

from app.routes import datasets, workflows, ptx, output, api, auth
from app.middleware.security import SecurityMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    
    # =============== STARTUP ===============
    logger.info(f"Starting {settings.app_name}...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")
    log_temporary_secrets(settings.temporary_secrets)
    
    try:
        # Initialize database connection with settings
        logger.info("Initializing database connection...")
        await db_config.connect(settings, [
            Dataset,FileDataset, MongoDataset, MysqlDataset,
            ApiDataset, ElasticDataset, PTXDataset, IProject, User, PasswordResetToken,
            ServiceChainData
        ])
            # Test Beanie après initialisation
        try:
            count = await Dataset.count()
            logger.info(f"Beanie test after init: {count} datasets found")
        except Exception as e:
            logger.error(f"Beanie test failed: {e}")

        # Encrypt plain text credentials and re-encrypt those using a previous key
        try:
            counts = await reencrypt_sensitive_fields()
            if counts["reencrypted"]:
                logger.info(f"{counts['reencrypted']} sensitive dataset field(s) re-encrypted with the current FIELD_ENCRYPTION_KEY")
            if counts["failed"]:
                logger.error(
                    f"{counts['failed']} sensitive dataset field(s) cannot be decrypted with any known key: "
                    "re-enter the credentials of these datasets"
                )
        except Exception as e:
            logger.error(f"Re-encryption of sensitive dataset fields failed: {e}", exc_info=True)
        
        # Ensure admin user exists (create default admin if no users exist)
        logger.info("Checking for admin user...")
        user_service = UserService()
        admin = None
        try:
            admin = await user_service.ensure_admin_exists()
            if admin:
                logger.info(f"Admin user available: {admin.username}")
        except Exception as e:
            logger.error(f"Failed to ensure admin exists: {e}", exc_info=True)
        
        # Run migration if config.ini exists
        if os.path.exists("./app/config.ini"):
            if admin:
                logger.info("Config.ini found, starting migration...")
                migration_success = await MigrationService.migrate_from_config_ini(admin)
                if migration_success:
                    logger.info("Migration completed successfully")
                else:
                    logger.warning("Migration completed with warnings")
            else:
                logger.error("Cannot run migration: Admin user not available")
        else:
            logger.info("No config.ini found, skipping migration")
        
        logger.info(f"{settings.app_name} startup completed successfully")
        
    except Exception as e:
        logger.critical(f"Critical error during startup: {e}", exc_info=True)
        raise
    
    yield
    
    # =============== SHUTDOWN ===============
    logger.info(f"Shutting down {settings.app_name}...")
    try:
        await db_config.disconnect()
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Data Analysis and Visualization Backend API",
    version="2.0.0",
    lifespan=lifespan,
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security middleware - Add this to monitor and limit suspicious requests
if settings.security_enabled:
    app.add_middleware(
        SecurityMiddleware,
        rate_limit=settings.security_rate_limit,
        time_window=settings.security_time_window
    )

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()
    
    logger.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    return response

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Request validation error handler"""
    logger.warning(f"Request validation error on {request.url}: {exc.errors()}")
    
    if settings.debug:
        logger.debug(f"Request body: {exc.body}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({
            "detail": exc.errors(), 
            "body": exc.body if settings.debug else "Hidden in production",
            "message": "Request validation failed"
        }),
    )

# Include ALL routers
app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(workflows.router)
app.include_router(ptx.router)
app.include_router(output.router)
app.include_router(api.router)

# Legacy route
@app.get("/get_image")
async def get_image():
    """Get image endpoint"""
    from pathlib import Path
    from fastapi.responses import FileResponse
    
    image_path = Path("uploads/img/dbeaver3.png")
    if not image_path.is_file():
        logger.warning(f"Image not found: {image_path}")
        return {"error": "Image not found on the server"}
    return FileResponse(image_path)

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "environment": settings.environment,
        "version": "2.0.0"
    }

# Debug endpoints - Only available in development
if settings.debug and settings.environment != "production":
    @app.get("/debug/settings")
    async def debug_settings():
        """Debug endpoint to check settings"""
        return {
            "app_name": settings.app_name,
            "environment": settings.environment,
            "debug": settings.debug,
            "log_level": settings.log_level,
            "mongodb_url": settings.mongodb_url[:20] + "..." if len(settings.mongodb_url) > 20 else settings.mongodb_url,
            "database_name": settings.database_name,
            "cors_origins": settings.cors_origins,
            "upload_dir": settings.upload_dir,
            "max_file_size": settings.max_file_size,
            "security": {
                "enabled": settings.security_enabled,
                "rate_limit": settings.security_rate_limit,
                "time_window": settings.security_time_window
            }
        }

    @app.get("/debug/migration-status")
    async def migration_status():
        """Debug endpoint to check migration status"""
        try:
            datasets_count = await Dataset.count()
            workflows_count = await IProject.count()
            
            return {
                "mongodb_connected": True,
                "total_datasets": datasets_count,
                "total_workflows": workflows_count,
                "datasets_breakdown": {
                    "file": await FileDataset.count(),
                    "mongo": await MongoDataset.count(),
                    "mysql": await MysqlDataset.count(),
                    "api": await ApiDataset.count(),
                    "elastic": await ElasticDataset.count(),
                    "ptx": await PTXDataset.count()
                },
                "config_ini_exists": os.path.exists("./app/config.ini"),
                "config_ini_backup_exists": os.path.exists("./app/config.ini.backup"),
                "settings": {
                    "environment": settings.environment,
                    "debug": settings.debug,
                    "log_level": settings.log_level
                }
            }
        except Exception as e:
            logger.error(f"Error in migration status endpoint: {e}", exc_info=True)
            return {
                "mongodb_connected": False,
                "error": str(e),
                "environment": settings.environment
            }

    @app.post("/debug/create-config")
    async def create_config_ini():
        """Create config.ini from current database state"""
        try:
            from datetime import datetime
            import json
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"config_{timestamp}.ini"
            
            # Create the structure expected by MigrationService
            config_data = {
                "connections": [],
                "workflows": []
            }
            
            # Export datasets as connections - KEEP IDs for workflow references
            dataset_count = 0
            async for dataset in Dataset.find_all():
                dataset_count += 1
                
                # Convert dataset to dict but PRESERVE the _id as id
                dataset_dict = dataset.model_dump()
                
                # Convert MongoDB _id to string id (preserve for workflow references)
                if "_id" in dataset_dict:
                    dataset_dict["id"] = str(dataset_dict["_id"])
                    del dataset_dict["_id"]
                
                config_data["connections"].append(dataset_dict)
            
            # Export workflows - KEEP IDs and dataset references
            workflow_count = 0
            async for workflow in IProject.find_all():
                workflow_count += 1
                
                # Convert workflow to dict but PRESERVE the _id as id
                workflow_dict = workflow.model_dump()
                
                # Convert MongoDB _id to string id
                if "_id" in workflow_dict:
                    workflow_dict["id"] = str(workflow_dict["_id"])
                    del workflow_dict["_id"]
                
                config_data["workflows"].append(workflow_dict)
            
            # Write config file as JSON
            with open(f'./app/{filename}', 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            return {
                "success": True,
                "filename": filename,
                "datasets_exported": dataset_count,
                "workflows_exported": workflow_count,
                "message": f"Config file created: {filename}. Rename to config.ini to use for migration. IDs preserved for workflow references."
            }
            
        except Exception as e:
            logger.error(f"Error creating config file: {e}")
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,   # Reload for debug
        limit_max_request_size=10*settings.max_file_size,  # Convert to bytes
        log_level=settings.log_level.lower()
    )
