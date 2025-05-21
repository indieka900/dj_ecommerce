from rest_framework import permissions

class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow:
    - Admin users to have full access
    - Any user (including unauthenticated) to have read-only access
    """
    def has_permission(self, request, view):
        # Allow GET, HEAD, OPTIONS requests for anyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For write operations, require authenticated admin user
        return request.user and request.user.is_authenticated and request.user.role == 'Administrator'