from rest_framework import permissions

class IsOwnerCanEditAnyCanCreate(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it, but anyone to create the object.
    """
    def has_object_permission(self, request, view, obj):
        # GET, HEAD or OPTIONS requests: Only owner
        if request.method in permissions.SAFE_METHODS:
            return obj.owner == request.user
        # Anyone can create
        elif request.method == 'POST':
            return True
        # Write permissions are only allowed to the owner.
        else:
            return obj.owner == request.user

class IsCreatorCanView(permissions.DjangoObjectPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        #'POST': ['%(app_label)s.add_%(model_name)s'],
        'POST': [],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

class IsCreatorCanEdit(permissions.DjangoObjectPermissions):
    perms_map = {
        'GET': [],
        'OPTIONS': [],
        'HEAD': [],
        'POST': [],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }