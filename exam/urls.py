from django.urls import path
from .views import (
    admin_login,
    dashboard,
    create_exam,
    add_departments,
    add_rooms,
    upload_students,
    generate_seating,
    get_seating_data,
    lock_seating
)

urlpatterns = [
    path('', admin_login, name='admin_login'),
    path('dashboard/', dashboard, name='dashboard'),

    # STEP 1 - Create Exam
    path('create_exam/', create_exam, name='create_exam'),

    # STEP 2 - Add Departments + Paper
    path('add_departments/', add_departments, name='add_departments'),

    # STEP 3 - Add Rooms
    path('add_rooms/', add_rooms, name='add_rooms'),

    # STEP 4 - Upload Students
    path('upload_students/', upload_students, name='upload_students'),

    # STEP 5 - Seat Allocation (new)
    path('generate_seating/', generate_seating, name='generate_seating'),
    path('get_seating_data/<int:exam_id>/', get_seating_data, name='get_seating_data'),
    path('lock_seating/', lock_seating, name='lock_seating'),
]
