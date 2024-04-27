from django.contrib.auth import login
from . import models


class IPBasedAutoAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.ignored = {'/admin/'}

    def get_location(self, request) -> models.Location:
        # Get the IP address from the request
        ip = request.META.get('REMOTE_ADDR')
        try:
            location = models.Location.objects.get(ip_address=ip)
        except models.Location.DoesNotExist:
            print(f'location {ip} not yet exists. Remember location.')
            location = models.Location.objects.create(ip_address=ip)
        return location

    def __call__(self, request):
        for ignored in self.ignored:
            if request.path.startswith(ignored):
                return self.get_response(request)
        location = self.get_location(request)
        if not (hasattr(request, 'user') and request.user.is_authenticated):
            user = location.default_user
            if user is not None:
                login(request, user)
                print(f'auto login to {location} as {user}')
        return self.get_response(request)
