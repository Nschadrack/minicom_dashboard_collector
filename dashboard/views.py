from django.shortcuts import render

# Create your views here.
def dashboard(request):

    return render(request, "base_layout.html")
    # return render(request, 'document_viewer.html')
