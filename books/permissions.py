from rest_framework.permissions import BasePermission


class IsAdminOrLibrarian(BasePermission):
    """
    Read access for everyone.
    Write access only for Admins and Librarians.
    """

    def has_permission(self, request, view):

        # Allow public read operations
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        # Restrict write operations
        return (
            request.user.is_authenticated
            and request.user.role in ["ADMIN", "LIBRARIAN"]
        )