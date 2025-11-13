import requests
from rest_framework import status, generics, permissions
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from ..serializers import (
    UserSerializer,
    ForgotPasswordOtpSerializer,
    ResetPasswordSerializer,
)
from ..models import *
from rest_framework.permissions import AllowAny, IsAuthenticated
import random
from django.core.mail import send_mail
from HSM_AI import constants, settings, utils
from django.contrib.auth.hashers import check_password
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password
from authentication.models import *
import logging
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.tokens import AccessToken, TokenError
import json
from HSM_AI.helper.cloud_to_s3 import upload_base64_to_s3
import base64
from HSM_AI.helper.pagination import CustomPagination

logger = logging.getLogger(__name__)


class RegisterUser(APIView):
    @swagger_auto_schema(request_body=UserSerializer)
    def post(self, request):
        try:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                data = {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone_number": user.phone_number,
                    "country_code": user.country_code,
                    "role": user.role,
                }
                return utils.success_response(
                    message="User registered successfully.",
                    data=data,
                    status_code=status.HTTP_200_OK,
                    api_status_code=status.HTTP_200_OK,
                )

            # Collect first error message
            error_messages = []
            for field, errors in serializer.errors.items():
                for err in errors:
                    error_messages.append(f"{err}")
            error_message = (
                error_messages[0] if error_messages else "Validation failed."
            )
            return utils.error_response(
                message="User already exists",
                errors=error_message,
                status_code=status.HTTP_400_BAD_REQUEST,
                api_status_code=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return utils.error_response(
                message=f"Error: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST,
                api_status_code=status.HTTP_400_BAD_REQUEST,
            )


class LoginUser(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # encryptedData = request.data.get('payload')
        # decryptedData = utils.decrypt_data(encryptedData)
        # print("decryptedData : ",decryptedData)
        email = request.data.get("email")
        password = request.data.get("password")

        # Step 1: Validate presence of email and password
        if not email or not password:
            return Response(
                {"message": "Email and password are required.", "status": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Step 2: Authenticate user
        user = authenticate(request, email=email, password=password)

        # Step 3: If authenticated, return JWT tokens
        if user:
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Login successful.",
                    "data": {
                        "user_id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "token": {
                            "refresh": str(refresh),
                            "access": str(refresh.access_token),
                        },
                    },
                    "status": 200,
                },
                status=status.HTTP_200_OK,
            )

        # Step 4: If credentials are invalid
        return Response(
            {"message": "Invalid email or password.", "status": 400},
            status=status.HTTP_400_BAD_REQUEST,
        )


class SendForgotPasswordOtp(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return utils.error_response("Email is required")

        try:
            user = Users.objects.get(email=email, is_deleted=False)
        except Users.DoesNotExist:
            return utils.error_response("No user registered with this email.")

        otp = random.randint(100000, 999999)
        user.otp_code = str(otp)
        user.otp_created_at = timezone.now()
        user.save()

        # 📨 In production, send via email
        print("Generated OTP:", otp)

        return utils.success_response(
            message="Verification code sent successfully.", data={"email": user.email}
        )


class VerifyForgotPasswordOtp(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordOtpSerializer(data=request.data)
        if not serializer.is_valid():
            return utils.error_response("Invalid data", errors=serializer.errors)

        email = serializer.validated_data["email"]
        otp = str(serializer.validated_data["otp"])

        try:
            user = Users.objects.get(email=email, is_deleted=False)
        except Users.DoesNotExist:
            return utils.error_response("User not found.")

        if not user.is_otp_valid(otp):
            return utils.error_response("OTP is incorrect or expired.")

        # OTP is valid → clear it
        user.clear_otp()

        # Generate short-lived token (valid 5 min)
        token = AccessToken.for_user(user)
        token.set_exp(lifetime=timezone.timedelta(minutes=5))

        return utils.success_response(
            "OTP verified successfully.", data={"reset_token": str(token)}
        )


class ResetForgotPassword(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        reset_token = request.data.get("reset_token")
        new_password = request.data.get("new_password")

        if not reset_token or not new_password:
            return utils.error_response("reset_token and new_password are required.")

        try:
            # Decode token
            token = AccessToken(reset_token)
            user_id = token["user_id"]

            # Get user
            user = Users.objects.get(id=user_id, is_deleted=False)
        except (TokenError, Users.DoesNotExist):
            return utils.error_response("Invalid or expired reset token.")

        # Update password
        user.password = make_password(new_password)
        user.save()

        return utils.success_response("Password updated successfully.")


class GetUserDetails(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user  # Comes from token
            # If you're using custom user model, request.user will be instance of `Users`
            serializer = UserSerializer(user)

            return utils.success_response(
                message="User details fetched successfully.",
                data=serializer.data,
                status_code=status.HTTP_200_OK,
                api_status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            return utils.error_response(
                message="Failed to fetch user details.",
                errors=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
                api_status_code=status.HTTP_400_BAD_REQUEST,
            )


class AddUser(APIView):
    permission_classes = [IsAuthenticated]
    # authentication_classes = []
    # permission_classes = []

    @swagger_auto_schema(request_body=UserSerializer)
    def post(self, request):
        try:
            serializer = UserSerializer(data=request.data)

            if serializer.is_valid():
                user = serializer.save()

                data = {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone_number": user.phone_number,
                    "country_code": user.country_code,
                    "role": str(user.role.id) if user.role else None,
                    "role_name": getattr(user.role, "role_name", None),
                    "status": user.status,
                }

                return utils.success_response(
                    message="User added successfully.",
                    data=data,
                    status_code=status.HTTP_201_CREATED,
                    api_status_code=status.HTTP_201_CREATED,
                )

            # if validation failed, check specific cases
            if "email" in serializer.errors:
                if any(
                    "exists" in str(err).lower() for err in serializer.errors["email"]
                ):
                    return utils.error_response(
                        message="User already exists with this email.",
                        errors=serializer.errors,
                        status_code=status.HTTP_400_BAD_REQUEST,
                        api_status_code=status.HTTP_400_BAD_REQUEST,
                    )

            # missing fields case
            missing_fields = [
                field
                for field, errors in serializer.errors.items()
                if any("required" in str(err).lower() for err in errors)
            ]
            if missing_fields:
                return utils.error_response(
                    message=f"Missing required fields: {', '.join(missing_fields)}",
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST,
                    api_status_code=status.HTTP_400_BAD_REQUEST,
                )

            # other validation errors
            return utils.error_response(
                message="Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
                api_status_code=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return utils.error_response(
                message="Something went wrong",
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                api_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


""" Microsoft SSO """


class MicrosoftLogin(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response(
                {"message": "Authorization code is required.", "status": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # 1️⃣ Exchange code for token
            token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
            data = {
                "client_id": settings.MICROSOFT_CLIENT_ID,
                "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
            }
            token_response = requests.post(token_url, data=data).json()
            # print("Microsoft token response:", token_response)

            if "error" in token_response:
                return Response(
                    {
                        "message": "Invalid access.",
                        "errors": token_response.get(
                            "error_description", token_response.get("error")
                        ),
                        "status": 400,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            access_token = token_response.get("access_token")

            # 2️⃣ Fetch Microsoft user info
            user_info = requests.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {access_token}"},
            ).json()
            # print("user_info:", user_info)

            email = user_info.get("mail") or user_info.get("userPrincipalName")
            first_name = user_info.get("givenName")
            last_name = user_info.get("surname")

            if not email:
                return Response(
                    {
                        "message": "Microsoft account does not have an email.",
                        "status": 400,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 3️⃣ Check if user exists
            try:
                user = Users.objects.get(email=email, is_deleted=False)
            except Users.DoesNotExist:
                return Response(
                    {"message": "Not registered, please contact admin.", "status": 404},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # 4️⃣ Generate JWT tokens (same as normal login)
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Login successful.",
                    "data": {
                        "user_id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "token": {
                            "refresh": str(refresh),
                            "access": str(refresh.access_token),
                        },
                    },
                    "status": 200,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"message": f"Error during Microsoft login: {str(e)}", "status": 500},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


""" Drop Box SSO || List Folder & Filter || Download """


class DropboxTokenAPI(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response(
                {"message": "Authorization code is required.", "status": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Dropbox token exchange endpoint
            token_url = "https://api.dropboxapi.com/oauth2/token"
            data = {
                "code": code,
                "grant_type": "authorization_code",
                "client_id": settings.DROPBOX_CLIENT_ID,
                "client_secret": settings.DROPBOX_CLIENT_SECRET,
                "redirect_uri": settings.DROPBOX_REDIRECT_URI,
            }

            response = requests.post(token_url, data=data)
            token_response = response.json()
            # print("Dropbox token response:", token_response)

            # Check if Dropbox returned an error
            if "error" in token_response:
                return Response(
                    {
                        "message": "Failed to get access token from Dropbox.",
                        "errors": token_response,
                        "status": 400,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Return the token response directly
            return Response(
                {
                    "message": "Dropbox token retrieved successfully.",
                    "data": token_response,
                    "status": 200,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "message": f"Error during Dropbox token request: {str(e)}",
                    "status": 500,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DropboxListFilesAPI(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get("access_token")
        folder_path = request.data.get("path", "")  # "" = root if not given

        if not access_token:
            return Response(
                {"message": "Access token is required.", "status": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            url = "https://api.dropboxapi.com/2/files/list_folder"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            data = {
                "path": folder_path,  # can be "", "/MyFolder", "/MyFolder/Subfolder"
                "recursive": False,
            }
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            return Response(
                {
                    "message": "Files fetched successfully.",
                    "data": result,
                    "status": 200,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"message": f"Error fetching Dropbox files: {str(e)}", "status": 500},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DropboxDownloadFileAPI(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get("access_token")
        file_path = request.data.get("path")
        project_name = request.data.get("project_name", "default_project")

        if not access_token or not file_path:
            return Response(
                {"message": "Access token and file path are required.", "status": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            url = "https://content.dropboxapi.com/2/files/download"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Dropbox-API-Arg": json.dumps({"path": file_path}),
            }

            response = requests.post(url, headers=headers)

            if response.status_code != 200:
                return Response(
                    {
                        "message": "Failed to download file.",
                        "error": response.text,
                        "status": response.status_code,
                    },
                    status=response.status_code,
                )

            # Convert content → base64
            file_content_base64 = base64.b64encode(response.content).decode("utf-8")
            file_name = file_path.split("/")[-1]

            # Upload to S3 via custom helper
            s3_url = upload_base64_to_s3(file_content_base64, file_name, project_name)

            return Response(
                {
                    "message": "File downloaded from Dropbox and uploaded to S3.",
                    "data": {"file_name": file_name, "s3_url": s3_url},
                    "status": 200,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"message": f"Error downloading file: {str(e)}", "status": 500},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


""" Users """


class UserListCreateView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = Users.objects.filter(is_deleted=False).order_by("created_date")

        search_term = self.request.query_params.get("search")
        if search_term:
            queryset = queryset.filter(
                Q(first_name__icontains=search_term)
                | Q(last_name__icontains=search_term)
                | Q(email__icontains=search_term)
            )

        role_filter = self.request.query_params.get("role")
        if role_filter:
            # queryset = queryset.filter(role__role_name__iexact=role_filter)
            queryset = queryset.filter(role__id=role_filter)

        return queryset

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return utils.success_response(
                "Users fetched successfully.", serializer.data, status.HTTP_200_OK
            )
        except Exception as e:
            return utils.error_response("Failed to fetch users.", str(e), 500)

    @swagger_auto_schema(request_body=UserSerializer)
    def create(self, request, *args, **kwargs):
        try:
            email = request.data.get("email")
            if not email:
                return utils.error_response(
                    "Email is required.",
                    "Missing email in request.",
                    status.HTTP_400_BAD_REQUEST,
                )

            # Check for soft-deleted user
            deleted_user = Users.objects.filter(email=email, is_deleted=True).first()
            if deleted_user:
                serializer = self.get_serializer(
                    deleted_user, data=request.data, partial=True
                )
                if serializer.is_valid():
                    serializer.save(is_deleted=False)  # Reactivate user
                    return utils.success_response(
                        "User restored successfully.",
                        serializer.data,
                        status.HTTP_200_OK,
                    )
                return utils.error_response(
                    "Validation error while restoring user.",
                    serializer.errors,
                    status.HTTP_400_BAD_REQUEST,
                )

            # Create new user
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                return utils.success_response(
                    "User added successfully.", serializer.data, status.HTTP_201_CREATED
                )

            return utils.error_response(
                "Validation error.", serializer.errors, status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return utils.error_response(
                "Failed to create user.", str(e), status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Users.objects.filter(is_deleted=False)

    def retrieve(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            serializer = self.get_serializer(user)
            return utils.success_response(
                "User fetched successfully.", serializer.data, status.HTTP_200_OK
            )
        except Exception as e:
            return utils.error_response("Failed to fetch user.", str(e), 500)

    @swagger_auto_schema(request_body=UserSerializer)
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            user = self.get_object()
            serializer = self.get_serializer(user, data=request.data, partial=partial)

            if serializer.is_valid():
                serializer.save()
                return utils.success_response(
                    "User updated successfully.", serializer.data, status.HTTP_200_OK
                )

            return utils.error_response(
                "Validation error.", serializer.errors, status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return utils.error_response("Failed to update user.", str(e), 500)

    def destroy(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            user.is_deleted = True
            user.save()
            return utils.success_response(
                "User removed successfully.", {"id": str(user.id)}, status.HTTP_200_OK
            )
        except Exception as e:
            return utils.error_response("Failed to delete user.", str(e), 500)
