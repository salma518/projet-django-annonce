from django.core.cache import cache
import os
import random
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render, redirect
from django.views import View
from .forms import BaseProfileAdmin, InscriptionForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from .models import Administrateur, Favoris, Question, Reponses, Signal, User, Message,Categorie
from .forms import BaseProfileForm, InscriptionForm, BaseProfileFormAdmin
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate
from django.core.paginator import Paginator
import json
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.contrib import messages

# Create your views here.
# def home(request):
#  return render(request, 'base.html')

def inscription(request):
    
    if request.method == 'POST':
        form = InscriptionForm(request.POST, request.FILES)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Inscription réussie! Vous pouvez maintenant vous connecter.')
            return redirect('login_page')
        else:
         print(form.errors) 
    else:
        
        form = InscriptionForm()
        
    return render(request, 'Utilisateur/inscription.html', {'form': form})

class LoginPage(View):
   def get(self, request):
    # if 'adm' in request.path:
    #     return render(request, 'Administrateur/loginPage.html')
    return render(request, 'Utilisateur/login.html')


class AuthUtilisateur(View):
    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            sous_categories = Categorie.objects.exclude(parent=None)

            sous_categorie_id = request.GET.get('sous_categorie')
    
            if sous_categorie_id:
                annonces = Annonce.objects.filter(categorie_id=sous_categorie_id).order_by('-datePublication')
            else:
                annonces = Annonce.objects.all().order_by('-datePublication','-isPremieum')  # 6 dernières annonces par défaut

            annonces_non_signalees = annonces.exclude(id__in=Signal.objects.values('annonce_id')).order_by('-isPremieum')

            paginator = Paginator(annonces_non_signalees, 6)
            page_number = request.GET.get('page')
            annonces = paginator.get_page(page_number)

            return render(request, 'Utilisateur/homePage.html',{'annonces': annonces,'MEDIA_URL': settings.MEDIA_URL,"categories":sous_categories})  # Redirection après succès
        else:
            messages.error(request, 'Email ou mot de passe invalide.')
            return redirect('login_page')  # On retourne à la page de connexion

    def get(self, request):
        if request.user.is_authenticated:
            sous_categories = Categorie.objects.exclude(parent=None)
            sous_categorie_id = request.GET.get('sous_categorie')
    
            if sous_categorie_id:
                annonces = Annonce.objects.filter(categorie_id=sous_categorie_id).order_by('-datePublication')
                
            else:
                annonces = Annonce.objects.all().order_by('-datePublication')
            
            annonces_non_signalees = annonces.exclude(id__in=Signal.objects.values('annonce_id')).order_by('-isPremieum')
            
            paginator = Paginator(annonces_non_signalees, 6)
            page_number = request.GET.get('page')
            annonces = paginator.get_page(page_number)
                
            return render(request, 'Utilisateur/homePage.html', {
                'annonces': annonces,
                'MEDIA_URL': settings.MEDIA_URL,
                'categories': sous_categories
            })
        return redirect('home')

class LogoutView(View):
    def get(self, request):
        if request.user.is_authenticated:
            logout(request)
            return redirect('home')
            # return render(request, 'base.html', {'message': 'Vous avez été déconnecté avec succès.'})
        return render(request, 'Utilisateur/homePage.html')
        
def Profil_User(request, user_id):
    user = get_object_or_404(User, id=user_id)
    print(request.user.nom)
    # Pagination pour les annonces de l'utilisateur
    user_ads_list = Annonce.objects.filter(user_id=user.id).order_by('-datePublication')
    favoris = Favoris.objects.filter(user_id=user.id).count()
    paginator = Paginator(user_ads_list, 2)  # 6 annonces par page
    page_number = request.GET.get('page')
    user_ads = paginator.get_page(page_number)

    return render(request, 'Utilisateur/Profil_User.html', {
        'user': user,
        'user_ads': user_ads,
        'user_ads_count': user_ads_list.count(),
        'user_favorites_count':favoris,
        'categories': Categorie.objects.exclude(parent=None),
        'MEDIA_URL': settings.MEDIA_URL
    })

def Profil_modifier(request ):
    if request.method == 'POST':
        form = BaseProfileForm(request.POST, request.FILES, instance=request.user)
        
        if form.is_valid():
            form.save()
            return redirect('Profil_User',user_id=request.user.id)
        else:
            print(form.errors)
    else:
        form = BaseProfileForm(instance=request.user)
    return render(request, 'Utilisateur/Modifier_Profil.html', {'form': form})   

from .models import Annonce
import json
from django.core.files.storage import default_storage


from django.core.mail import send_mail
from django.conf import settings

#ajouter_annonce a ete modifie

def ajouter_annonce(request):
    if request.method == 'POST':
        
        # Récupération des données du formulaire
        titre = request.POST.get('titre')
        description = request.POST.get('description')
        categorie = request.POST.get('categorie_id')
        localisation = request.POST.get('localisation')
        prix = float(request.POST.get('prix'))
        is_premieum = request.POST.get('isPremieum') == 'on'
        
        # Gestion des images
        noms_images = []
        images = request.FILES.getlist('images')
        for image in images:
            path = os.path.join('annonces', image.name)
            saved_path = default_storage.save(path, image)
            noms_images.append(saved_path)
        
        # Création de l'annonce avec statut 'en_attente'
        annonce = Annonce.objects.create(
            titre=titre,
            description=description,
            prix=prix,
            user=request.user,
            categorie_id=categorie,
            isPremieum=is_premieum,  
            localisation=localisation,
            images=noms_images
        )

        messages.success(request,'Votre annonce a été soumise pour validation par un administrateur')
        
        return redirect('home_user')

from .forms import ModifierAnnonceForm

def modifier_annonce(request, annonce_id):
    annonce = get_object_or_404(Annonce, id=annonce_id)
    
    if request.method == 'POST':
        form = ModifierAnnonceForm(request.POST, instance=annonce)
        if form.is_valid():
            form.save()
            messages.success(request, "L'annonce a été mise à jour avec succès!")
            return redirect('mes_annonces')
        else:
            print("Erreurs du formulaire:", form.errors)

    else:
        form = ModifierAnnonceForm(instance=annonce)
    
    return render(request, 'Utilisateur/Modifier_Anc.html', {'form': form,'annonce': annonce})

def afficher_annonce_categorie(request,categorie_id):

    annonces = Annonce.objects.filter(categorie_id=categorie_id)
    return render(request, 'Utilisateur/test.html', {
        'annonces': annonces,
        'MEDIA_URL': settings.MEDIA_URL
})

def mes_annonces(request):
    annonces_list = Annonce.objects.filter(user=request.user).order_by('-datePublication')
    
    # Pagination - 6 annonces par page
    paginator = Paginator(annonces_list, 8)
    page_number = request.GET.get('page')
    annonces = paginator.get_page(page_number)
    
    categories = Categorie.objects.exclude(parent=None)
    return render(request, 'Utilisateur/Mes_annonces.html', {
        'annonces': annonces,
        'total_validee':annonces_list.filter(statut = True).count(),
        'total_non_validee':annonces_list.filter(statut = False).count(),
        'categories': categories,
        'MEDIA_URL': settings.MEDIA_URL
    })

from .models import Annonce

def home(request):
    categories = Categorie.objects.all()
    sous_categorie_id = request.GET.get('sous_categorie')
    
    if sous_categorie_id:
        annonces_list = Annonce.objects.filter(categorie_id=sous_categorie_id).order_by('-datePublication')
    else:
        annonces_list = Annonce.objects.all().order_by('-datePublication')

    annonces_list = annonces_list.order_by('-isPremieum')    
    
    # Pagination - 6 annonces par page
    paginator = Paginator(annonces_list, 6)
    page_number = request.GET.get('page')
    annonces = paginator.get_page(page_number)
    
    return render(request, 'base.html', {
        'annonces': annonces,
        'categories': categories,
        'MEDIA_URL': settings.MEDIA_URL,
        'selected_sous_categorie': int(sous_categorie_id) if sous_categorie_id else None
    })

from django.shortcuts import get_object_or_404

# class detail_annonce(View):
#     def get(self, request, annonce_id):
#         annonce = get_object_or_404(Annonce, id=annonce_id)

#         return render(request, 'Utilisateur/detail_annonce.html',
#                        {'annonce': annonce,
#                         'user_ads_count': Annonce.objects.filter(user_id = request.user.id).count(),
#                         'MEDIA_URL': settings.MEDIA_URL})
    



# class EnvoyerMessageAuUser(View):
#     def get(self,request,user_id):
#         userMessages = Message.objects.filter(userIdSource=request.user.id,userIdDesti=user_id)
#         user_des = User.objects.get(id = user_id)
#         return render(request,"Utilisateur/interfaceChat.html",{"user_actif":user_des,"userMessages":userMessages})
    
#     def post(self,request,user_id):
#         contenu = request.POST.get("contenu")
#         user_des = request.POST.get("user_id")
#         print(user_des)
#         Message.objects.create(
#             userIdDesti_id = user_des,
#             contenu=contenu,
#             userIdSource_id = request.user.id,
#         )
#         return redirect(f"/user/messages/{user_id}")
    


class AjouterAuxFavoris(LoginRequiredMixin, View):
    login_url = '/login/'

    def post(self, request, annonce_id):
        annonce = get_object_or_404(Annonce, id=annonce_id)
        
        if annonce is not None:
            favori_existant = Favoris.objects.filter(user_id=request.user.id, annonce_id=annonce.id).first()
            
            if not favori_existant:
                # Create a new favorite entry
                Favoris.objects.create(user_id=request.user.id, annonce_id=annonce.id)
                messages.success(request, 'Annonce ajouté aux favoris avec succès!')
                return redirect('favoris') 
            
            else:
                messages.info(request, 'Ce annonce est déjà dans vos favoris.')
                return redirect('home_user')
              
        else:
            messages.error(request, 'Annonce non trouvé.')
            return redirect('home_user')
        
class SupprimerDesFavoris(LoginRequiredMixin, View):
    login_url = '/login/'

    def post(self, request, annonce_id):
        favori_item = get_object_or_404(Favoris, user_id=request.user.id, annonce_id=annonce_id)
        favori_item.delete()
        messages.success(request, 'Annonce retiré des favoris avec succès!')
        return redirect('favoris')
    
class AfficherFavoris(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        favoris = Favoris.objects.filter(user=request.user).select_related('annonce')
        return render(request, 'Utilisateur/favoris.html', {
            'favoris': favoris,
            'MEDIA_URL': settings.MEDIA_URL
        })

def rechercher_annonce(request):
    query = request.GET.get('q', '')
    
    if query:
        Annonces = Annonce.objects.filter(
        Q(titre__icontains=query) |
        Q(user__nom__icontains=query) |
        Q(user__prenom__icontains=query)
        ).select_related('user')

        
    else:
        Annonces = Annonces.objects.all()
    
    annonces_non_signalees = Annonces.exclude(id__in=Signal.objects.values('annonce_id'))  

    paginator = Paginator(annonces_non_signalees, 8)  # Show 10 books per page
    page_number = request.GET.get('page')
    annonces = paginator.get_page(page_number)

    

    return render(request, 'Utilisateur/homePage.html', {'annonces': annonces, 'query': query, 'MEDIA_URL': settings.MEDIA_URL}) 

from django.shortcuts import redirect
from django.contrib import messages

def signaler_annonce(request):
    if request.method == 'POST':
        annonce_id = request.POST.get('annonce_id')
        raison = request.POST.get('raison')
        
        if not annonce_id or not raison:
            messages.error(request, "Veuillez fournir une raison de signalement")
            return redirect('home_user')
        
        try:
            annonce = Annonce.objects.get(id=annonce_id)
            # Créer le signalement
            Signal.objects.create(
                description=raison,
                user_id=request.user.id,
                annonce_id=annonce_id
            )
            

            messages.success(request, "L'annonce a été signalée et sera examinée")
            return redirect('home_user')
            
        except Annonce.DoesNotExist:
            messages.error(request, "Annonce non trouvée")
            return redirect('home_user')
    
    return redirect('home_user')

def supprimer_anc( request, annonce_id):
    annonce = get_object_or_404(Annonce, user_id=request.user.id, id=annonce_id)
    annonce.delete()
    return redirect('home_user')

#admin views
#ajouter_annonce a ete modifie

class LoginPageAdmin(View):
   def get(self, request):
    return render(request, 'Administrateur/login.html')

def register_admin(request):
    if request.method == 'POST':
        form = BaseProfileFormAdmin(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login_admin')
    else:
        form = BaseProfileFormAdmin()
    return render(request, 'Administrateur/register.html', {'form': form})

from django.core.paginator import Paginator

class AuthAdministrateur(View):
    def _get_common_context(self, user):
        """Génère le contexte commun pour les deux méthodes (GET et POST)"""
        annonces_en_attente = Annonce.objects.filter(statut=False).order_by('-datePublication')
        paginator = Paginator(annonces_en_attente, 4)  # 6 annonces par page
        
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return {
            'annonces': Annonce.objects.all().order_by('-datePublication')[:6],
            'annonce_validee': Annonce.objects.filter(statut=True).count(),
            'annonce_non_validee': annonces_en_attente.count(),
            'Annonces_en_attentes': page_obj,  # Utilisez page_obj au lieu du queryset complet
            'MEDIA_URL': settings.MEDIA_URL,
            'categories': Categorie.objects.all(),
            'Administrateur': user,
            'user': User.objects.all(),
            'user_count': User.objects.all().count(),
        }

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        admin = authenticate(request, username=email, password=password)
        
        if admin is not None:
            login(request, admin)
            return render(request, 'Administrateur/homePage.html', self._get_common_context(admin))
        else:
            messages.error(request, 'Email ou mot de passe invalide.')
            return redirect('login_admin')

    def get(self, request):
        if request.user.is_authenticated:
            return render(request, 'Administrateur/homePage.html', self._get_common_context(request.user))
        return redirect('login_admin')


def Profil_Admin(request, Admin_id):
    return render(request, 'Administrateur/Profil_Admin.html', {
        'Admin': get_object_or_404(Administrateur, id=Admin_id),
        'Annonce_en_attente': Annonce.objects.filter(statut=False).count(),
        'Annonces_signales':Annonce.objects.filter(
        id__in=Signal.objects.values_list('annonce_id', flat=True)
    ).select_related('user', 'categorie').prefetch_related('signals').count(),
        'MEDIA_URL':settings.MEDIA_URL
    })


def get_Utilisateur(request):
    
    context = {
        'users': [
            {
                'id': user.id,
                'image': user.image,
                'nom': user.nom,
                'prenom': user.prenom,   # Meilleure pratique que user.nom
                'email': user.email,
                'is_active': user.is_active,
                'annonces_validees': user.annonces.filter(statut = True).count(), 
                'annonces_non_validees': user.annonces.filter(statut = False).count(), 
                'last_login': user.last_login,  # Ajout utile pour l'admin
                'date_joined': user.date_joined,  # Ajout utile pour l'admin
            }
            for user in User.objects.all()
        ],
        'total_users': User.objects.all().count(),  # Ajout statistique utile
        'active_users': User.objects.filter(is_active=True).count(),  # Ajout statistique
    }
    
    return render(request, 'Administrateur/Utilisateurs.html', context)

def get_Utilisateur_Profil(request, user_id):

    active_tab = request.GET.get('tab', 'validated')

    annonces_enatt = Annonce.objects.filter(user_id = user_id, statut = False).order_by('-datePublication')
    annonces_val = Annonce.objects.filter(user_id = user_id, statut = True).order_by('-datePublication')

    paginator = Paginator(annonces_enatt, 2)  # 10 annonces par page
    page_number = request.GET.get('page')
    annonces_enatt = paginator.get_page(page_number)

    paginator = Paginator(annonces_val, 2)  # 10 annonces par page
    page_number = request.GET.get('page')
    annonces_val = paginator.get_page(page_number)


    return render(request, 'Administrateur/Details_utilisateur.html', {
        'user': get_object_or_404(User, id=user_id),
        'annonces_val': annonces_val,
        'annonces_enatt':annonces_enatt,
        'active_tab':active_tab,
        'annonces_validees': Annonce.objects.filter(user_id = user_id, statut = True).count(),
        'annonces_non_validees': Annonce.objects.filter(user_id = user_id, statut = False).count(),
        'categories' : Categorie.objects.all(),
        'MEDIA_URL':settings.MEDIA_URL
    })

def preview_annonce(request, annonce_id):
    annonce = get_object_or_404(Annonce, id=annonce_id)

    context = {
        'annonce': annonce,
        'MEDIA_URL': settings.MEDIA_URL
    }
    return render(request, 'Administrateur/previsualiser_annonce.html', context)

from django.core.mail import send_mail
from django.contrib import messages

def approve_annonce(request):
    if request.method == 'POST':
        print(request.POST.get('annonce_id'))
        annonce = get_object_or_404(Annonce, id=request.POST.get('annonce_id'))
        annonce.statut = True
        annonce.save()
        
        # Envoi d'email
        send_mail(
            subject=f"Annonce approuvée : {annonce.titre}",
            message=f"Votre annonce '{annonce.titre}' a été approuvée.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[annonce.user.email]
        )
        
        messages.success(request, "L'annonce a été approuvée avec succès.")
        return redirect('home_admin')
    
    messages.error(request, "L'annonce n'a pas été approuvée .")
    return redirect('home_admin')

def reject_annonce(request):
    if request.method == 'POST':
        annonce = get_object_or_404(Annonce, id=request.POST.get('annonce_id'))
        reason = request.POST.get('rejection_reason', 'Raison non spécifiée')

        # Envoi d'email
        send_mail(
            subject=f"Annonce rejetée : {annonce.titre}",
            message=f"Votre annonce a été rejetée. Raison : {reason}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[annonce.user.email],  
        )
        
        annonce.delete()
        messages.success(request, "L'annonce a été rejetée avec succès.")
        return redirect('home_admin')
    
    messages.error(request, "L'annonce n'a pas été rejetée.")
    return redirect('home_admin')

def Chercher_user(request):
    query = request.GET.get('q')  # Récupère le terme de recherche
    users = None

    if query:
        # Filtre les utilisateurs dont le nom contient la requête (insensible à la casse)
        users = User.objects.filter(nom=query)
    context = {
        'users': [
            {
                'id': user.id,
                'image': user.image,
                'nom': user.nom,
                'prenom': user.prenom,   # Meilleure pratique que user.nom
                'email': user.email,
                'is_active': user.is_active,
                'annonces_validees': user.annonces.filter(statut = True).count(), 
                'annonces_non_validees': user.annonces.filter(statut = False).count(), 
                'last_login': user.last_login,  # Ajout utile pour l'admin
                'date_joined': user.date_joined,  # Ajout utile pour l'admin
            }
            for user in users
        ],
        'total_users': User.objects.all().count(),  # Ajout statistique utile
        'active_users': User.objects.filter(is_active=True).count(),  # Ajout statistique
    }
    return render(request, 'Administrateur/Utilisateurs.html', context)

def get_Annonces(request):
    annonces_list = Annonce.objects.all().order_by('-datePublication')
    paginator = Paginator(annonces_list, 6)  # 10 annonces par page
    page_number = request.GET.get('page')
    Annonces = paginator.get_page(page_number)
    context = {
        'Annonces':Annonces,
        'annonce_non_validee':Annonce.objects.filter(statut = False ).count(),
        'annonce_validee':Annonce.objects.filter(statut = True ).count(),
        'annonce_signalee':Annonce.objects.filter(statut = False ).count(),
        'MEDIA_URL': settings.MEDIA_URL

    }
    
    return render(request, 'Administrateur/Annonces.html', context)

def Chercher_annonces(request):
    query = request.GET.get('q')

    if query:
        Annonces = Annonce.objects.filter(
            Q(titre__icontains=query) |
            Q(user__nom__icontains=query) |
            Q(user__prenom__icontains=query)
        ).select_related('user')  # Optimise le chargement des users
    
    if request.user.email.endswith('adm.com'):

        return render(request, 'Administrateur/Annonces.html',
            {'Annonces': Annonces,
            'annonce_non_validee':Annonce.objects.filter(statut = False ).count(),
            'annonce_validee':Annonce.objects.filter(statut = True ).count(),
            'annonce_signalee':Annonce.objects.filter(statut = False ).count(),
            'MEDIA_URL': settings.MEDIA_URL})
    else:
        Annonces = Annonces.filter(user_id = request.user.id)
        return render(request, 'Utilisateur/Profil_User.html', {
        'user': request.user,
        'user_ads': Annonces,
        'categories': Categorie.objects.exclude(parent=None),
        'MEDIA_URL': settings.MEDIA_URL
    })
        
def Chercher_annonces_statut(request):
    statut = request.GET.get('Statut', '')

    if statut == '1' :
        annonces_queryset = Annonce.objects.filter(statut= True)

    elif statut == '0' :
        annonces_queryset = Annonce.objects.filter(statut = False)

    else:
        annonces_queryset = Annonce.objects.all()
    
    paginator = Paginator(annonces_queryset, 10)  # 10 annonces par page
    page_number = request.GET.get('page')
    Annonces = paginator.get_page(page_number)
    
    
    if request.user.email.endswith('adm.com'):
        return render(request, 'Administrateur/Annonces.html', {
            'Annonces': annonces_queryset,
            'annonce_non_validee':Annonce.objects.filter(statut = False ).count(),
            'annonce_validee':Annonce.objects.filter(statut = True ).count(),
            'annonce_signalee':Annonce.objects.filter(statut = False ).count(),
            'MEDIA_URL': settings.MEDIA_URL
        })
    else:
        annonces_queryset = annonces_queryset.filter(user_id = request.user.id)
        paginator = Paginator(annonces_queryset, 2)  # 10 annonces par page
        page_number = request.GET.get('page')
        Annonces = paginator.get_page(page_number)
        
        return render(request, 'Utilisateur/Profil_User.html', {
        'user': request.user,
        'user_ads': Annonces,
        'categories': Categorie.objects.exclude(parent=None),
        'MEDIA_URL': settings.MEDIA_URL
    })
    
def Profil_modifier_Admin(request ):
    if request.method == 'POST':
        form = BaseProfileAdmin(request.POST, request.FILES, instance=request.user)
        
        if form.is_valid():
            form.save()
            return redirect('Profil_Admin',Admin_id=request.user.id)
        else:
            print(form.errors)
    else:
        form = BaseProfileAdmin(instance=request.user)
    return render(request, 'Administrateur/Modifier.html', {'form': form})   

class PasswordResetAdmin(LoginRequiredMixin,View):
    def get(self, request, admin_id):
        # Vérifie que l'admin existe avant d'afficher le formulaire
        get_object_or_404(Administrateur, id=admin_id)
        return render(request, 'Administrateur/password_Admin.html', {'admin_id': admin_id})

    def post(self, request, admin_id):
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validation des champs vides
        if not password or not confirm_password:
            messages.error(request, "Veuillez remplir tous les champs")
            return render(request, 'Administrateur/password_Admin.html', {'admin_id': admin_id})
        
        # Validation de la correspondance
        if password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas")
            return render(request, 'Administrateur/password_Admin.html', {'admin_id': admin_id})
        
        
        # Récupération et mise à jour sécurisée
        admin = Administrateur.objects.get(id=admin_id)
        admin.password = make_password(password)
        admin.save()
        
        messages.success(request, "Mot de passe réinitialisé avec succès")
        return redirect('login_admin') 
    
from django.shortcuts import render
from django.conf import settings
from .models import Signal, Annonce

def get_Annonces_Signalees(request):
    
    annonces_signalees = Annonce.objects.filter(
        id__in=Signal.objects.values_list('annonce_id', flat=True)
    ).select_related('user', 'categorie').prefetch_related('signals')
    
   
    annonces_data = []
    for annonce in annonces_signalees:
        
        signalements = annonce.signals.all()
        descriptions = [signal.description for signal in signalements]
        
        annonces_data.append({
            'annonce': annonce,
            'descriptions': descriptions,
            'nb_signalements': signalements.count()
        })
    
 

    context = {
        'Annonces': annonces_data,  
        'total_annonces_signalees': annonces_signalees.count(),
        'MEDIA_URL': settings.MEDIA_URL
    }
    
    return render(request, 'Administrateur/Signalement.html', context)

def supprimer_annonce(request, annonce_id):
   
    annonce = get_object_or_404(Annonce, id=annonce_id)
    send_mail(
        subject=f"Annonce Signalee : {annonce.titre}",
        message=f"Votre annonce a été signalée. ",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[annonce.user.email],  
    )
    annonce.delete()
    return redirect('Annonces_signalees')

from django.shortcuts import render
from django.db.models import Count
from django.utils import timezone
from .models import Annonce, Categorie


def get_statistics(request):
    # Récupérer toutes les annonces
    annonces = Annonce.objects.filter(statut = True)
    total_annonces = annonces.count()

    # Distribution par catégorie
    annonces_by_category = annonces.values('categorie__nom').annotate(
        count=Count('id')
    ).order_by('-count')

    # Calculer les pourcentages pour les catégories
    for category in annonces_by_category:
        category['percentage'] = (category['count'] / total_annonces * 100) if total_annonces > 0 else 0

    # Distribution par prix
    price_ranges = [
        {'label': '0-100 €', 'min': 0, 'max': 100},
        {'label': '101-500 €', 'min': 101, 'max': 500},
        {'label': '501-1000 €', 'min': 501, 'max': 1000},
        {'label': '1001-5000 €', 'min': 1001, 'max': 5000},
        {'label': '5000+ €', 'min': 5001, 'max': float('inf')}
    ]

    # Calculer le nombre d'annonces par tranche de prix
    for range_info in price_ranges:
        count = annonces.filter(
            prix__gte=range_info['min'],
            prix__lte=range_info['max'] if range_info['max'] != float('inf') else 999999
        ).count()
        range_info['count'] = count
        range_info['percentage'] = (count / total_annonces * 100) if total_annonces > 0 else 0

    # Distribution par localisation
    locations = annonces.values('localisation').annotate(
        count=Count('id')
    ).order_by('-count')

    # Calculer les pourcentages pour les localisations
    for location in locations:
        location['percentage'] = (location['count'] / total_annonces * 100) if total_annonces > 0 else 0

    context = {
        'annonces_by_category': annonces_by_category,
        'price_ranges': price_ranges,
        'locations': locations,
        'last_update': timezone.now(),
    }

    return render(request, 'Administrateur/statistiques.html', context)

def validation_annonces(request):
    annonces_list = Annonce.objects.filter(statut=False).order_by('-datePublication')
    paginator = Paginator(annonces_list, 10)  # 10 annonces par page
    page_number = request.GET.get('page')
    annonces_en_attente = paginator.get_page(page_number)

    return render(request, 'Administrateur/Validation_Annonces.html', {
        'annonces_en_attente': annonces_en_attente,
        'MEDIA_URL': settings.MEDIA_URL
    })


def home_user(request):
    annonces = Annonce.objects.filter(statut=True).order_by('-date_creation')
    categories = Categorie.objects.all()
    
    # Calculer le total des messages reçus
    total_messages = Message.objects.filter(
        userIdDesti=request.user
    ).count()
    
    paginator = Paginator(annonces, 6)
    page = request.GET.get('page')
    annonces = paginator.get_page(page)
    
    return render(request, 'Utilisateur/homePage.html', {
        'annonces': annonces,
        'categories': categories,
        'total_messages': total_messages,
        'MEDIA_URL': settings.MEDIA_URL
    })

class PasswordResetRequestView(View):
    def get(self, request):
        return render(request, 'Utilisateur/password_reset_request.html')
    
    def post(self, request):
        email = request.POST.get('email')
        
        # Vérifier si l'email existe
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Aucun compte trouvé avec cet email.")
            return render(request, 'User/password_reset_request.html')
        
        # Générer un code de vérification (6 chiffres)
        verification_code = str(random.randint(1000, 9999))
        
        # Stocker le code dans le cache (valide 15 minutes)
        cache.set(f'password_reset_{email}', verification_code, 120)
        
        # Envoyer l'email
        subject = "Réinitialisation de votre mot de passe"
        message = f"""
        Bonjour,
        
        Vous avez demandé à réinitialiser votre mot de passe. 
        Voici votre code de vérification :
        
        {verification_code}
        
        Ce code est valable pendant 2 minutes.
        
        Si vous n'avez pas fait cette demande, veuillez ignorer cet email.
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        # Stocker l'email en session pour les étapes suivantes
        request.session['reset_email'] = email
        
        messages.success(request, "Un code de vérification a été envoyé à votre adresse email.")
        return redirect('verify_reset_code')

class PasswordResetCodeVerifyView(View):
    def get(self, request):
        if 'reset_email' not in request.session:
            return redirect('password_reset_request')
        return render(request, 'Utilisateur/verify_reset_code.html')
    
    def post(self, request):
        email = request.session.get('reset_email')
        user_code = request.POST.get('verification_code')
        cached_code = cache.get(f'password_reset_{email}')
        
        if not cached_code or cached_code != user_code:
            messages.error(request, "Code invalide ou expiré.")
            return render(request, 'Utilisateur/verify_reset_code.html')
        
        # Code valide, passer à l'étape de confirmation
        return redirect('password_reset_confirm')

class PasswordResetConfirmView(View):
    def get(self, request):
        if 'reset_email' not in request.session:
            return redirect('password_reset_request')
        return render(request, 'Utilisateur/password_reset_confirm.html')
    
    def post(self, request):
        email = request.session.get('reset_email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'Utilisateur/password_reset_confirm.html')
        
        try:
            user = User.objects.get(email=email)
            user.password = make_password(password)
            user.save()
            
            # Nettoyer la session et le cache
            del request.session['reset_email']
            cache.delete(f'password_reset_{email}')
            
            messages.success(request, "Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter.")
            return redirect('login_page')
        except User.DoesNotExist:
            messages.error(request, "Une erreur est survenue. Veuillez réessayer.")
            return redirect('password_reset_request')
        


class PasswordResetAdmin(LoginRequiredMixin,View):
    def get(self, request, admin_id):
        # Vérifie que l'admin existe avant d'afficher le formulaire
        get_object_or_404(Administrateur, id=admin_id)
        return render(request, 'Administrateur/password_reset_request.html', {'admin_id': admin_id})

    def post(self, request, admin_id):
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validation des champs vides
        if not password or not confirm_password:
            messages.error(request, "Veuillez remplir tous les champs")
            return render(request, 'Administrateur/password_reset_request.html', {'admin_id': admin_id})
        
        # Validation de la correspondance
        if password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas")
            return render(request, 'Administrateur/password_reset_request.html', {'admin_id': admin_id})
        
        
        # Récupération et mise à jour sécurisée
        admin = Administrateur.objects.get(id=admin_id)
        admin.password = make_password(password)
        admin.save()
        
        messages.success(request, "Mot de passe réinitialisé avec succès")
        return redirect('login_admin') 



class repondreAuquestion(View):
    def get(self,request,question_id,annonce_id):
        question = Question.objects.get(id=question_id)
        annonce = get_object_or_404(Annonce, id=annonce_id)
        questions = Question.objects.filter(annonce_id=annonce_id)
        return render(request,"Utilisateur/detail_annonce.html",{"question_actif":question,'MEDIA_URL': settings.MEDIA_URL,"questions":questions,"annonce":annonce})
    def post(self,request,question_id,annonce_id):
        Reponses.objects.create(
            user_id=request.user.id,
            question_id=question_id,
            contenu = request.POST.get("contenu")
        )
        return redirect(f"/annonce/{annonce_id}")

def afficherResponse(request,question_id,annonce_id):
    question = Question.objects.get(id=question_id)
    annonce = get_object_or_404(Annonce, id=annonce_id)
    questions = Question.objects.filter(annonce_id=annonce_id)
    reponses = Reponses.objects.filter(question_id = question_id);
    return render(request,"Utilisateur/detail_annonce.html",{"reponses_actif":reponses,'MEDIA_URL': settings.MEDIA_URL,"questions":questions,"annonce":annonce})


def AjouterQuestion(request,annonce_id):
    Question.objects.create(
        contenu = request.POST.get("contenu"),
        user_id = request.user.id,
        annonce_id = annonce_id
    )
    messages.success(request,"Commentaire ajouté")
    return redirect(f"/annonce/{annonce_id}")

class detail_annonce(View):
    def get(self, request, annonce_id):
        annonce = get_object_or_404(Annonce, id=annonce_id)
        questions = Question.objects.filter(annonce_id=annonce_id)
        #reponses = Reponses.objects.filter(annonce_id=annonce_id)
        
        return render(request, 'Utilisateur/detail_annonce.html',
                        {'annonce': annonce,
                         'questions':questions,
                        'user_ads_count': Annonce.objects.filter(user_id = request.user.id).count(),
                        'MEDIA_URL': settings.MEDIA_URL})

from django.db.models import Q
from django.db.models import Count

def afficherUserMessages(request):
    listeUserMessage = User.objects.filter(
        messages_envoyes__userIdDesti=request.user.id,
        # messages_recus__userIdSource=user_id
    ).annotate(
        num_messages=Count('messages_envoyes')
    ).distinct()
    return render(request, 'Utilisateur/Reçu_message.html',{'listeUserMessage': listeUserMessage})

def messageRecuNonLus(request, user_id):
    userM = User.objects.get(id=user_id)
    print("id user connecte", request.user.id)
    print("id user params", user_id)
    listeUserMessage = User.objects.filter(
        messages_envoyes__userIdDesti=request.user
    ).annotate(
        num_messages=Count('messages_envoyes')
    ).distinct()
    messages = Message.objects.filter(
        Q(userIdDesti=request.user, userIdSource=userM) | 
        Q(userIdDesti=userM, userIdSource=request.user)
    ).order_by('date_envoi')
    
    for ms in messages:
        print(ms.contenu)
    
    return render(request, 'Utilisateur/Reçu_message.html', {
        'messagesUser': messages,
        "user_actif": userM,
        'listeUserMessage': listeUserMessage
    })

def ajoutermessage(request):
    contenu = request.POST.get("contenu")
    user_des = request.POST.get("user_id")
    Message.objects.create(
        userIdDesti_id = user_des,
        contenu=contenu,
        userIdSource_id = request.user.id,
    )
    return redirect(f"/messages/{user_des}")

class EnvoyerMessageAuUser(View):
    def get(self,request,user_id):
        userMessages = Message.objects.filter(Q(userIdDesti=request.user, userIdSource=user_id) | Q(userIdDesti=user_id, userIdSource=request.user))
        user_des = User.objects.get(id = user_id)
        return render(request,"Utilisateur/interfaceChat.html",{"user_actif":user_des,"userMessages":userMessages})
    
    def post(self,request,user_id):
        contenu = request.POST.get("contenu")
        user_des = request.POST.get("user_id")
        print(user_des)
        Message.objects.create(
            userIdDesti_id = user_des,
            contenu=contenu,
            userIdSource_id = request.user.id,
        )
        return redirect(f"/user/messages/{user_id}")
    
def messageUserAuUser(request,user_id):
    print(user_id)
    # return HttpResponse(user_id)
    listeUser = Message.objects.filter(userIdSource = request.user.id)
    # # user = User.objects.get(id=userid)
    userMessages = Message.objects.filter(userIdSource=request.user.id,userIdDesti=user_id)
    return render(request,"Utilisateur/interfaceChat.html",{"listeUser":listeUser})

