from django.apps import AppConfig


class InfraConfig(AppConfig):
    name = "id_infra"

    def ready(self):
        from id_infra import signals  # noqa: F401
