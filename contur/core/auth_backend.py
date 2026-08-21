from core.models import CustomUser


class EncryptedUsernameBackend:

    def authenticate(self, request, username=None, password=None, **kwargs): 
        """
        Authenticates a user by decrypted username and password
        Args:
            request: The request object
            username: The username to authenticate
            password: The password to authenticate
            **kwargs: Arbitrary keyword arguments
        Returns:
            The user if authenticated, otherwise None
        """   
        if username is None or password is None:
            return None

        user = CustomUser.get_by_username(username)
        if user is None:
            return None

        if user.check_password(password):
            return user

        return None

    def get_user(self, user_id):
        """
        Gets a user by id
        Args:
            user_id: The id of the user to get
        Returns:
            The user if found, otherwise None
        """
        try:
            return CustomUser.objects.get(pk=user_id, deleted=False)
        except CustomUser.DoesNotExist:
            return None
