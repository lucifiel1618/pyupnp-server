# from django.conf import settings
from django.views.generic import TemplateView
from django.contrib.auth import logout
from django.shortcuts import redirect


class Index(TemplateView):
    template_name = 'index.html'


class AccountProfile(TemplateView):
    template_name = 'account_profile.html'


def logout_view(request):
    logout(request)
    # Get the page from where the user logged out.
    next_page = request.GET.get('next', '/')
    return redirect(next_page)
