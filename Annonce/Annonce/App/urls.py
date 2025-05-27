from django.urls import path
from . import views 



urlpatterns=[
    #Utilisateur
    path('',views.home,name='home'),
    path('inscription/', views.inscription ,name='inscription'),

    path('login/', views.LoginPage.as_view(), name='login_page'),           # GET: formulaire
    path('home/', views.AuthUtilisateur.as_view(), name='home_user'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('annonces/ajouter/', views.ajouter_annonce, name='ajouter_annonce'),
    path('annonces/', views.afficher_annonce_categorie, name='liste_annonce'),
    path('mes-annonces/', views.mes_annonces, name='mes_annonces'),
    path('modifier_annonce/<int:annonce_id>/', views.modifier_annonce, name='modifier_annonce'),

    path('annonce/<int:annonce_id>/', views.detail_annonce.as_view(), name='detail_annonce'),

    path('Profil_User/<int:user_id>', views.Profil_User, name='Profil_User'),
    path('Profil_Modifier/', views.Profil_modifier, name='Profil_Modifier'),

    path('user/messages/<int:user_id>',views.EnvoyerMessageAuUser.as_view(), name='messageToUser'),
    path('message/<user_id>',views.messageUserAuUser, name='chat_actif'),


    path('ajouter_favoris/<int:annonce_id>/', views.AjouterAuxFavoris.as_view(), name='ajouter_favoris'),
    path('supprimer_favoris/<int:annonce_id>/', views.SupprimerDesFavoris.as_view(), name='supprimer_des_favoris'),
    path('favoris/', views.AfficherFavoris.as_view(), name='favoris'),

    path('recherche/', views.rechercher_annonce, name='rechercher_annonce'),

    path('signaler/', views.signaler_annonce, name='signaler_annonce'),

    path('Supp/<int:annonce_id>', views.supprimer_anc, name='Supprimer_anc'),

    #Admin

    path('inscription_Admin/', views.register_admin ,name='inscription_Admin'),
    path('login_adm/', views.LoginPageAdmin.as_view(), name='login_admin'),           # GET: formulaire
    path('home_Admin/', views.AuthAdministrateur.as_view(), name='home_admin'),
    path('logout/', views.LogoutView.as_view(), name='logout'),


    path('Profil_Admin/<int:Admin_id>', views.Profil_Admin, name='Profil_Admin'),
    path('Profil_Modifier_Admin/', views.Profil_modifier_Admin, name='Profil_Modifier_Admin'),

    path('Utilisateurs/',views.get_Utilisateur,name='Utilisateurs'),
    path('Utilisateur/<int:user_id>',views.get_Utilisateur_Profil,name='Utilisateur'),

    path('preview/<int:annonce_id>/', views.preview_annonce, name='preview_annonce'),
    path('approve/', views.approve_annonce, name='approve_annonce'),
    path('reject/', views.reject_annonce, name='reject_annonce'),

    path('Chercher_user/', views.Chercher_user, name='Chercher_user'),

    path('Annonces/',views.get_Annonces,name='Annonces'),
    path('Chercher_annonces/', views.Chercher_annonces, name='Chercher_annonce'),
    path('Chercher_annonce_statut/', views.Chercher_annonces_statut, name='Chercher_annonce_statut'),

    path('Signalement/',views.get_Annonces_Signalees,name='Annonces_signalees'),
    path('Supprimer/<int:annonce_id>', views.supprimer_annonce, name='Supprimer'),

    #path('password-reset/<int:admin_id>', views.PasswordResetAdmin.as_view(), name='password_reset_request'),

    path('statistics/', views.get_statistics, name='statistiques'),
    path('validation-annonces/', views.validation_annonces, name='validation_annonces'),

    path('question/<int:annonce_id>/', views.AjouterQuestion, name='questionadd'),
    path('reponse/<int:question_id>/<annonce_id>', views.repondreAuquestion.as_view(), name='reponseqst'),
    path('reponses/<int:question_id>/<annonce_id>', views.afficherResponse, name='reponsesqst'),
    
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/verify-code/',views.PasswordResetCodeVerifyView.as_view(), name='verify_reset_code'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    path('password-reset-admin/<int:admin_id>/', views.PasswordResetAdmin.as_view(), name='password_reset_admin'),

    path('mes-messages/',views.afficherUserMessages, name='messages-recu'),
    path('messages/<user_id>/',views.messageRecuNonLus, name='messages-recu-actif'),
    path('save-messages/',views.ajoutermessage, name='save-messages'),

    path('user/messages/<int:user_id>',views.EnvoyerMessageAuUser.as_view(), name='messageToUser'),
    path('message/<user_id>',views.messageUserAuUser, name='chat_actif'),
   


]