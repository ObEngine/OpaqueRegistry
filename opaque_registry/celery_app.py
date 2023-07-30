from celery import Celery

celery_app = Celery("sandcodex")

celery_app.autodiscover_tasks(["sandcodex.async_tasks.sandbox"])
