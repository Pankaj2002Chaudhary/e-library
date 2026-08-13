from rest_framework.permissions import BasePermission


class IsAdminOrLibrarian(BasePermission):
    """
    Analytics are accessible only
    to Admins and Librarians.
    """

    def has_permission(
        self,
        request,
        view
    ):

        return (
            request.user.is_authenticated
            and request.user.role in [
                "ADMIN",
                "LIBRARIAN"
            ]
        )