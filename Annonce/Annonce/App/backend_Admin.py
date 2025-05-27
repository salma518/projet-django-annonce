from django.contrib.auth.backends import BaseBackend
from .models import Administrateur

class AuthAdministrateur(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        
        try:
            
            user = Administrateur.objects.get(email=username)
           
          
            if user.check_password(password):
            
             return user
        except Administrateur.DoesNotExist:
            return None
    def get_user(self,user_id):
        try:
            return Administrateur.objects.get(id=user_id)
        except Administrateur.DoesNotExist:
            return None
        


