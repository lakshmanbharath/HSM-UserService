from authentication.models import Users

def get_user_name_by_email(email: str) -> str:
    """
    Returns the full name of a user given their email.
    Falls back to the email if the user is not found or has no name.
    """
    try:
        user = Users.objects.get(email=email)
        full_name = " ".join(filter(None, [user.first_name, user.last_name]))
        return full_name or user.username or email
    except Users.DoesNotExist:
        return email

