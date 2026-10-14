class Session:
    """
    Stores information about the currently logged-in user.
    """

    current_user = None

    @classmethod
    def login(cls, user):
        """
        Store logged-in user information.
        """
        cls.current_user = user

    @classmethod
    def logout(cls):
        """
        Remove the currently logged-in user.
        """
        cls.current_user = None

    @classmethod
    def is_logged_in(cls):
        """
        Check whether a user is currently logged in.
        """
        return cls.current_user is not None

    @classmethod
    def get_user(cls):
        """
        Return the currently logged-in user.
        """
        return cls.current_user