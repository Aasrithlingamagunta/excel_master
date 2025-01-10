from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_file_view, name='upload'),  # Handle file uploads
    path('question/', views.qa_view, name='question'),  # Handle Q&A requests
    path('', views.render_main_page, name='main'),  # Main page view
]
