from django.urls import path
from .views.authviews import (
    RegisterUser, 
    LoginUser,
    SendForgotPasswordOtp,
    VerifyForgotPasswordOtp,
    ResetForgotPassword,
    GetUserDetails,
    AddUser,
    MicrosoftLogin,
    # DropboxTokenAPI,
    # DropboxListFilesAPI,
    # DropboxDownloadFileAPI,
    UserListCreateView,
    UserDetailView
    )
from .views.emailviews import *

urlpatterns = [
    path('register/', RegisterUser.as_view(), name='register'),
    path('login/', LoginUser.as_view(), name='login'),
    path("login/microsoft/", MicrosoftLogin.as_view(), name="login-microsoft"),
    # path("login/dropbox/", DropboxTokenAPI.as_view(), name="login-dropbox"),
    # path("files/dropbox/", DropboxListFilesAPI.as_view(), name="files-dropbox"),
    # path("files/dropbox/download/", DropboxDownloadFileAPI.as_view(), name="download-dropbox"),
    path('profile/', GetUserDetails.as_view(), name='profile'),
    path('forgot-password/email/', SendForgotPasswordOtp.as_view(), name='forgot-password-email'),
    path('forgot-password/verify/', VerifyForgotPasswordOtp.as_view(), name='forgot-password-verify'),
    path('forgot-password/reset/', ResetForgotPassword.as_view(), name='forgot-password-reset'),
    path("add-user/", AddUser.as_view(), name="add-user"),
    path("users/", UserListCreateView.as_view(), name="user-list-create"),
    path("users/<uuid:pk>/", UserDetailView.as_view(), name="user-detail"),
]
