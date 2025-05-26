from django.apps import AppConfig


class PetClinicAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'petclinic_app'

    
    def ready(self):
        import petclinic_app.signals  # Make sure to import your signals.py file here