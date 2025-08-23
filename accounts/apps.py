from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    
    def ready(self):
        import accounts.signals
    
        # from django.db.utils import OperationalError
        # from accounts.models import CustomUser as User

        # def create_superuser_if_not_exists():
        #     try:
        #         if not User.objects.filter(email="test@test.com").exists():
        #             User.objects.create_superuser("test@test.com", "joseph1234")
        #             print("Superuser created")
        #     except OperationalError:
        #         pass

        # # Call this function on startup
        # create_superuser_if_not_exists()
