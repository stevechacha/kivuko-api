from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        from django.db.models.signals import post_migrate

        from api.signals import seed_demo_data

        post_migrate.connect(seed_demo_data, sender=self)
