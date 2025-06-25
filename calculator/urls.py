from django.urls import path
from . import views

urlpatterns = [
    path('departments/', views.list_departments),
    path('send-otp/', views.send_otp),
    path('verify-otp/', views.verify_otp),
    path('subjects/<int:sem_num>/<str:dept_code>/', views.subjects_by_semester_and_department),
    path("semesters/", views.list_semesters),
    path("save-result/", views.save_results),
    path("user-history/", views.user_historys),
    path('admin-results/',views.admin_all_results),
]
