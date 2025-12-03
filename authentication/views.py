# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm, SignUpForm
from django.contrib.auth import logout

from django.shortcuts import render, redirect, get_object_or_404
from .models import Profile
from .forms import ProfileForm
import sweetify


def profile_edit(request, pk=None):
    profile = Profile.objects.all()
    if pk:
        profile = get_object_or_404(Profile, pk=pk)
    else:
        profile = None

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect('authentication:profile', pk=profile.pk)
    else:
        form = ProfileForm(instance=profile)
        profile = Profile.objects.all()

    return render(request, 'accounts/profile/profile.html', {'form': form, 'profile':profile})


def user_logout(request):
    logout(request)
    return redirect('authentication:login') 
def login_view(request):
    form = LoginForm(request.POST or None)

    msg = None

    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                sweetify.success(request, f'Selamat anda berhasil Login {username}', extra_tags="success")
                return redirect("/")
            else:
                msg = 'Invalid username or password!'
        else:
            msg = 'An error occurred!.'

    return render(request, "accounts/login.html", {"form": form, "msg": msg})


def register_user(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)

            msg = 'User created - please <a href="/login">login</a>.'
            success = True

            # return redirect("/login/")

        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form, "msg": msg, "success": success})
