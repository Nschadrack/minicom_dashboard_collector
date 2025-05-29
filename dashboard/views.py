from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def dashboard(request):
    return render(request, "welcome/internal_overview.html")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def welcome(request):
    today = datetime.now()
    hour = today.hour

    # Determine the appropriate greeting based on the time
    if 0 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    today = today.strftime("It's %A, %d %B %Y  %H:%M:%S")
    context = {
        "user": request.user,
        "title": "Welcome",
        "today": today,
        "greeting": f"{greeting}, {request.user.get_full_name()}"
    }

    return render(request, "welcome/welcome.html", context=context)
