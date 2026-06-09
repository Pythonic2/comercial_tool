from django.apps import AppConfig


class ComercialConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "comercial"
    
    def ready(self):
        """Registrar signals quando a aplicação está pronta."""
        import comercial.signals
