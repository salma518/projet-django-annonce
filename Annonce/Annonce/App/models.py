from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.utils import timezone
from django.contrib.auth.hashers import make_password

# class Categorie(models.Model):
#     nom = models.CharField(max_length=30)

#     def __str__(self):
#         return self.nom  

class Categorie(models.Model):
    nom = models.CharField(max_length=30)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sous_categories')

    def __str__(self):
        return self.nom
    
    def est_parent(self):
        return self.parent is None

class User(AbstractBaseUser, PermissionsMixin):
    image = models.ImageField(upload_to='images/', max_length=255, blank=True, null=True)
    nom = models.CharField(max_length=30)
    prenom = models.CharField(max_length=30)
    numeroTelephone = models.CharField(max_length=30)
    email = models.EmailField(max_length=30)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Correction pour les conflits avec auth.User
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_permissions_set',
        related_query_name='custom_user_permissions',
    )

    REQUIRED_FIELDS = ['nom', 'prenom', 'numeroTelephone']
    USERNAME_FIELD = 'email'

    def save(self, *args, **kwargs):
    # Si le mot de passe est en texte brut, le hacher
        if not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

class Administrateur(AbstractBaseUser, PermissionsMixin):
    image = models.ImageField(max_length=255, upload_to='admin/')
    nom = models.CharField(max_length=30)
    prenom = models.CharField(max_length=30)
    email = models.EmailField(max_length=30)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    groups = models.ManyToManyField(
        Group,
        related_name='admin_set',
        blank=True,
        help_text='The groups this admin belongs to.',
        related_query_name='admin',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='admin_permissions',
        blank=True,
        help_text='Specific permissions for this admin.',
        related_query_name='admin',
    )
    
    REQUIRED_FIELDS = ['nom', 'prenom']
    USERNAME_FIELD = 'email'

    def save(self, *args, **kwargs):
    # Si le mot de passe est en texte brut, le hacher
        if not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

class Annonce(models.Model):
    images = models.JSONField(default=list) 
    titre = models.CharField(max_length=30)
    description = models.TextField(max_length=100)
    prix = models.FloatField()
    datePublication = models.DateTimeField(default=timezone.now)
    statut = models.BooleanField(default=False)
    localisation = models.CharField(max_length=255,default='Casablanca')
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='annonces',  # Changé de 'user' à 'annonces'
        db_constraint=True,
        default=None
    )
    categorie = models.ForeignKey(
        Categorie, 
        on_delete=models.CASCADE, 
        related_name='annonces',  # Changé de 'categorie' à 'annonces'
        db_constraint=True,
        default=None
    )
    isPremieum = models.BooleanField(default=False)

class Question(models.Model):
    contenu = models.TextField(max_length=100)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='questions',  # Changé de 'user' à 'questions'
        db_constraint=True,
        default=None
    )
    annonce = models.ForeignKey(
        Annonce, 
        on_delete=models.CASCADE, 
        related_name='ann',
        db_constraint=True,
        default=None
    )

class Reponses(models.Model):
    contenu = models.TextField(max_length=100)
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE, 
        related_name='reponses',  # Changé de 'question' à 'reponses'
        db_constraint=True,
        default=None
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reponses_user',  # Changé de 'user' à 'reponses_user'
        db_constraint=True,
        default=None
    )

class Signal(models.Model):
    description = models.TextField(max_length=100)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='signals',  # Changé de 'user' à 'signals'
        db_constraint=True,
        default=None
    )
    annonce = models.ForeignKey(
        Annonce, 
        on_delete=models.CASCADE, 
        related_name='signals',  # Changé de 'annonce' à 'signals'
        db_constraint=True,
        default=None
    )

class Message(models.Model):
    userIdDesti = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='messages_recus',  # Changé de 'user_desti' à 'messages_recus'
        db_constraint=True,
        default=None
    )
    userIdSource = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='messages_envoyes',  # Changé de 'user_source' à 'messages_envoyes'
        db_constraint=True,
        default=None
    )
    contenu = models.TextField(max_length=100)
    date_envoi = models.DateTimeField(default=timezone.now)


class Favoris(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoris')
    annonce = models.ForeignKey(Annonce, on_delete=models.CASCADE, related_name='favoris')