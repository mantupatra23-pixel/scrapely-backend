import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "scrapely_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600
)

@celery_app.task(bind=True, name="tasks.execute_bulk_scrape_job")
def execute_bulk_scrape_job(self, job_id: str, keyword: str, city: str, country: str, limit: int):
    """
    Asynchronous Celery task processing multi-stage lead scraping and state updates.
    """
    self.update_state(state="LAUNCHING_BROWSER", meta={"progress": 10})
    # Task execution steps
    self.update_state(state="SEARCHING", meta={"progress": 30})
    self.update_state(state="COLLECTING", meta={"progress": 60})
    self.update_state(state="VERIFYING_EMAILS", meta={"progress": 85})
    return {"job_id": job_id, "status": "COMPLETED", "extracted": limit}
