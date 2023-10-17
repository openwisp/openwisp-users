class UserPasswordExpired(Exception):
    """The user's password is expired and requires changing."""

    def __init__(self, user=None, *args):
        self.user = user
        super().__init__(*args)
