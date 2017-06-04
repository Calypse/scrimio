from django.apps import AppConfig


class MmBaseConfig(AppConfig):
    name = 'mm_base'

    def ready(self):
        import mm_base.signals.handlers
