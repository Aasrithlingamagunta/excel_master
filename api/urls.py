from django.urls import path
from .views import render_main_page, upload_file_view, qa_view   # Correctly import the function from `views.py`

urlpatterns = [
    path('', render_main_page, name='main_page'),
    path('upload/', upload_file_view, name='upload_file'),
    path('question/', qa_view, name='qa_view'),
    # Render the main HTML
]
