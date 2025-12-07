"""
Main application entry point for the Podcast Manager.

This module initializes the FastAPI application, sets up database connections,
configures logging, and wires together all components.
"""

import click
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from pathlib import Path

from podcastmanager.config import get_settings
from podcastmanager.db.database import init_db, get_db_manager
from podcastmanager.services.file_manager import init_file_manager
from podcastmanager.tasks.worker import init_scheduler
from podcastmanager.utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Initialize database
    logger.info(f"Initializing database: {settings.database_url}")
    db_manager = init_db(settings.database_url, echo=settings.debug)

    # Create tables if they don't exist (for development)
    # In production, use Alembic migrations instead
    if settings.debug:
        logger.warning("Debug mode: Creating database tables")
        await db_manager.create_tables()

    # Initialize file manager
    logger.info(f"Initializing file manager: {settings.download_base_path}")
    init_file_manager(settings.download_base_path)

    # Start background task scheduler
    logger.info("Starting background task scheduler")
    scheduler = init_scheduler()
    scheduler.start()

    logger.info(f"Server starting on {settings.host}:{settings.port}")

    yield

    # Shutdown
    logger.info("Shutting down application")

    # Stop background scheduler
    logger.info("Stopping background task scheduler")
    scheduler.stop()

    # Close database connections
    await db_manager.close()
    logger.info("Database connections closed")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    settings = get_settings()

    # Set up logging
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file,
    )

    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A modern podcast manager for Plex Media Server",
        lifespan=lifespan,
    )

    # Mount static files
    static_path = Path(__file__).parent.parent.parent / "frontend" / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    # Set up templates
    template_path = Path(__file__).parent.parent.parent / "frontend" / "templates"
    if template_path.exists():
        app.state.templates = Jinja2Templates(directory=str(template_path))

    # Register API routes
    from podcastmanager.api.routes import router
    app.include_router(router)

    # Add health check endpoint
    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
        }

    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with basic info."""
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/api/health",
        }

    return app


# Create the app instance
app = create_app()


@click.group()
def cli():
    """Podcast Manager CLI."""
    pass


@cli.command()
@click.option("--host", default=None, help="Host to bind to")
@click.option("--port", default=None, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload (development)")
def serve(host: str, port: int, reload: bool):
    """Start the Podcast Manager web server."""
    import uvicorn

    settings = get_settings()

    # Override settings if provided
    if host is None:
        host = settings.host
    if port is None:
        port = settings.port

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "podcastmanager.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.log_level.lower(),
    )


@cli.command()
async def init_db_command():
    """Initialize the database (create tables)."""
    settings = get_settings()
    setup_logging(log_level=settings.log_level)

    logger.info("Initializing database...")
    db_manager = init_db(settings.database_url, echo=True)

    try:
        await db_manager.create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    finally:
        await db_manager.close()


@cli.command()
@click.option("--yes", is_flag=True, help="Skip confirmation")
async def reset_db(yes: bool):
    """Reset the database (WARNING: Deletes all data!)."""
    settings = get_settings()
    setup_logging(log_level=settings.log_level)

    if not yes:
        click.confirm(
            "This will DELETE ALL DATA in the database. Are you sure?",
            abort=True,
        )

    logger.warning("Resetting database...")
    db_manager = init_db(settings.database_url, echo=True)

    try:
        await db_manager.drop_tables()
        logger.info("Database tables dropped")

        await db_manager.create_tables()
        logger.info("Database tables recreated")

        logger.success("Database reset complete")
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        raise
    finally:
        await db_manager.close()


if __name__ == "__main__":
    cli()
