from core.models import CustomUser


class EncryptedUsernameBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        user = CustomUser.get_by_username(username)
        if user is None:
            return None

        if user.check_password(password):
            return user

        return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id, deleted=False)
        except CustomUser.DoesNotExist:
            return None
