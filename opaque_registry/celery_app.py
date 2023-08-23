from celery import Celery

celery_app = Celery("opaque_registry")

celery_app.autodiscover_tasks(["opaque_registry.async_tasks"])
