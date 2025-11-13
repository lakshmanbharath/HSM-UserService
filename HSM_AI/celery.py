# import os
# from celery import Celery
# from celery.schedules import crontab

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HSM_AI.settings")

# app = Celery("HSM_AI")
# app.config_from_object("django.conf:settings", namespace="CELERY")
# app.autodiscover_tasks()

# ## Celery Beat schedule (runs every 10 seconds)
# # app.conf.beat_schedule = {
# #     'print-every-10-seconds': {
# #         'task': 'provider.tasks.fetch_faxes_for_all_users',
# #         'schedule': 50.0,  # <-- every 10 seconds
# #     },
# # }

# # app.conf.beat_schedule = {
# #     'fetch-faxes-every-2-minutes': {
# #         'task': 'provider.tasks.fetch_faxes_for_all_users',
# #         'schedule': crontab(minute='*/2'),  # every 2 mins
# #     },
# # }