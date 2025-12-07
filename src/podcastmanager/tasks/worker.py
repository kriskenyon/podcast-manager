"""
Background task worker using APScheduler.

This module sets up and manages the background task scheduler for
periodic jobs like feed refresh, download processing, and cleanup.
"""

from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from podcastmanager.config import get_settings


class TaskScheduler:
    """
    Manages background tasks using APScheduler.

    Provides methods to start, stop, and manage scheduled jobs for
    automated podcast management tasks.
    """

    def __init__(self):
        """Initialize the task scheduler."""
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.settings = get_settings()

    def start(self):
        """
        Start the background task scheduler.

        This creates and starts the APScheduler instance with configured jobs.
        """
        if self.scheduler is not None:
            logger.warning("Scheduler already running")
            return

        logger.info("Starting background task scheduler...")

        # Create scheduler
        self.scheduler = AsyncIOScheduler(
            timezone="UTC",
            job_defaults={
                "coalesce": True,  # Combine missed runs
                "max_instances": 1,  # Only one instance per job at a time
                "misfire_grace_time": 3600,  # 1 hour grace period
            },
        )

        # Add jobs
        self._add_jobs()

        # Start the scheduler
        self.scheduler.start()
        logger.success("Background task scheduler started")

    def stop(self):
        """
        Stop the background task scheduler.

        Shuts down the scheduler and waits for running jobs to complete.
        """
        if self.scheduler is None:
            logger.warning("Scheduler not running")
            return

        logger.info("Stopping background task scheduler...")
        self.scheduler.shutdown(wait=True)
        self.scheduler = None
        logger.success("Background task scheduler stopped")

    def _add_jobs(self):
        """
        Add scheduled jobs to the scheduler.

        Configures and adds all background jobs with their intervals.
        """
        from podcastmanager.tasks.jobs import (
            cleanup_old_episodes_job,
            process_download_queue_job,
            refresh_all_podcasts_job,
        )

        # Job 1: Refresh all podcast feeds
        # Check for new episodes periodically
        self.scheduler.add_job(
            refresh_all_podcasts_job,
            trigger=IntervalTrigger(seconds=self.settings.feed_refresh_interval),
            id="refresh_podcasts",
            name="Refresh Podcast Feeds",
            replace_existing=True,
            next_run_time=datetime.utcnow(),  # Run immediately on startup
        )
        logger.info(
            f"Scheduled feed refresh job (interval: {self.settings.feed_refresh_interval}s)"
        )

        # Job 2: Process download queue
        # Process any pending downloads
        self.scheduler.add_job(
            process_download_queue_job,
            trigger=IntervalTrigger(seconds=300),  # Every 5 minutes
            id="process_downloads",
            name="Process Download Queue",
            replace_existing=True,
            next_run_time=datetime.utcnow(),  # Run immediately on startup
        )
        logger.info("Scheduled download queue processor (interval: 300s)")

        # Job 3: Cleanup old episodes
        # Remove old episodes based on podcast settings
        if self.settings.auto_cleanup_enabled:
            self.scheduler.add_job(
                cleanup_old_episodes_job,
                trigger=IntervalTrigger(seconds=self.settings.cleanup_interval),
                id="cleanup_episodes",
                name="Cleanup Old Episodes",
                replace_existing=True,
            )
            logger.info(
                f"Scheduled cleanup job (interval: {self.settings.cleanup_interval}s)"
            )

    def get_jobs(self):
        """
        Get information about scheduled jobs.

        Returns:
            List of job information dictionaries
        """
        if self.scheduler is None:
            return []

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time,
                    "trigger": str(job.trigger),
                }
            )
        return jobs

    def pause_job(self, job_id: str) -> bool:
        """
        Pause a scheduled job.

        Args:
            job_id: ID of the job to pause

        Returns:
            True if paused successfully, False otherwise
        """
        if self.scheduler is None:
            return False

        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause job {job_id}: {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job.

        Args:
            job_id: ID of the job to resume

        Returns:
            True if resumed successfully, False otherwise
        """
        if self.scheduler is None:
            return False

        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume job {job_id}: {e}")
            return False

    def trigger_job(self, job_id: str) -> bool:
        """
        Manually trigger a job to run immediately.

        Args:
            job_id: ID of the job to trigger

        Returns:
            True if triggered successfully, False otherwise
        """
        if self.scheduler is None:
            return False

        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.utcnow())
                logger.info(f"Triggered job: {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to trigger job {job_id}: {e}")
            return False


# Global scheduler instance
_scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """
    Get the global task scheduler instance.

    Returns:
        TaskScheduler instance

    Raises:
        RuntimeError: If scheduler hasn't been initialized
    """
    global _scheduler
    if _scheduler is None:
        raise RuntimeError("Task scheduler not initialized")
    return _scheduler


def init_scheduler() -> TaskScheduler:
    """
    Initialize the global task scheduler.

    Returns:
        TaskScheduler instance
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler
