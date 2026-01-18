
from django.shortcuts import  redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Exam, DepartmentExam, Room, Student,SeatAllocation 
import pandas as pd



def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, "exam/admin_login.html", {
                "error": "Invalid credentials"
            })

    return render(request, "exam/admin_login.html")


@login_required
def dashboard(request):
    return render(request, "exam/dashboard.html")


# =======================
# STEP 1: Create Exam
# =======================
@csrf_exempt
def create_exam(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            date = data.get('date')
            session = data.get('session')

            # Save exam
            exam = Exam.objects.create(
                name=name,
                date=date,
                session=session
            )

            # Return exam_id to frontend
            return JsonResponse({'status': 'success', 'exam_id': exam.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status':'error', 'message':'Invalid request method'})


# =======================
# STEP 2: Add Departments + Paper
# =======================
@csrf_exempt
def add_departments(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            exam_id = data.get('exam_id')
            departments = data.get('departments')  # Array of dept dicts

            # Validation: min 2, max 5
            if len(departments) < 2 or len(departments) > 5:
                return JsonResponse({'status':'error', 'message':'Select 2-5 departments'})

            # Get exam
            exam = get_object_or_404(Exam, id=exam_id)

            # Save each department row
            for dept in departments:
                DepartmentExam.objects.create(
                    exam=exam,
                    department=dept['department'],
                    paper_name=dept['paper_name'],
                    paper_code=dept['paper_code']
                )

            return JsonResponse({'status':'success'})
        except Exception as e:
            return JsonResponse({'status':'error', 'message': str(e)})
    return JsonResponse({'status':'error', 'message':'Invalid request method'})


# =======================
# STEP 3: Add Rooms
# =======================
@csrf_exempt
def add_rooms(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            exam_id = data.get('exam_id')
            rooms = data.get('rooms')  # Array of room dicts

            exam = get_object_or_404(Exam, id=exam_id)

            for r in rooms:
                Room.objects.create(
                    exam=exam,
                    building=r['building'],
                    room_number=r['room_number'],
                    capacity=r['capacity']
                )

            return JsonResponse({'status':'success'})
        except Exception as e:
            return JsonResponse({'status':'error', 'message': str(e)})
    return JsonResponse({'status':'error', 'message':'Invalid request method'})


# =======================
# STEP 4: Add Students
# =======================

@csrf_exempt
def upload_students(request):
    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        department = request.POST.get('department')
        file = request.FILES.get('file')

        if not all([exam_id, department, file]):
            return JsonResponse({'status': 'error', 'message': 'Missing parameters'})

        try:
            exam = get_object_or_404(Exam, id=exam_id)

            # Read Excel file
            df = pd.read_excel(file)

            # Expected columns: Roll Number | Registration Number | Name | Department
            expected_cols = {'Roll Number', 'Registration Number', 'Name', 'Department'}
            if not expected_cols.issubset(df.columns):
                return JsonResponse({'status': 'error', 'message': 'Invalid Excel format. Columns missing.'})

            # Normalize and save
            for _, row in df.iterrows():
                Student.objects.create(
                    exam=exam,
                    department=row['Department'],
                    roll_number=str(row['Roll Number']).strip(),
                    registration_number=str(row['Registration Number']).strip(),
                    name=row['Name'].strip()
                )

            return JsonResponse({'status': 'success', 'message': f'{len(df)} students uploaded for {department}'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def generate_seating(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            exam_id = data.get('exam_id')
            exam = get_object_or_404(Exam, id=exam_id)

            if exam.seating_locked:
                return JsonResponse({'status': 'error', 'message': 'Seating is locked. Cannot regenerate.'})

            students = list(Student.objects.filter(exam=exam))
            rooms = list(Room.objects.filter(exam=exam))

            if not students or not rooms:
                return JsonResponse({'status': 'error', 'message': 'No students or rooms found.'})

            # Remove old allocations
            SeatAllocation.objects.filter(exam=exam).delete()

            import random
            from string import ascii_uppercase

            random.shuffle(students)
            student_index = 0

            # Define fixed seat pattern (A1–H5)
            row_labels = list(ascii_uppercase[:8])  # A–H
            all_possible_seats = [f"{row}{col}" for row in row_labels for col in range(1, 6)]  # A1–H5

            for room in rooms:
                capacity = int(room.capacity)
                available_seats = all_possible_seats.copy()
                random.shuffle(available_seats)  # Shuffle seat positions randomly for this room

                for i in range(capacity):
                    if student_index >= len(students) or i >= len(available_seats):
                        break

                    seat_label = available_seats[i]
                    row_label = seat_label[0]
                    col_number = int(seat_label[1:])

                    student = students[student_index]
                    SeatAllocation.objects.create(
                        exam=exam,
                        student=student,
                        room=room,
                        session=exam.session,
                        row=row_label,
                        column=col_number,
                        seat_label=seat_label
                    )
                    student_index += 1

            # Prepare response data
            rooms_data = []
            for room in rooms:
                seats = SeatAllocation.objects.filter(room=room).select_related('student')
                seat_list = [{
                    'seat_label': s.seat_label,
                    'reg_no': s.student.registration_number,
                    'dept': s.student.department
                } for s in seats]
                rooms_data.append({
                    'room': f"{room.building}-{room.room_number}",
                    'capacity': room.capacity,
                    'seats': seat_list
                })

            return JsonResponse({'status': 'success', 'message': 'Seats allocated randomly', 'rooms': rooms_data})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def lock_seating(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            exam_id = data.get('exam_id')
            exam = get_object_or_404(Exam, id=exam_id)

            exam.seating_locked = True
            exam.save()

            return JsonResponse({'status': 'success', 'message': 'Seating arrangement locked successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
def get_seating_data(request, exam_id):
    try:
        exam = get_object_or_404(Exam, id=exam_id)
        rooms = Room.objects.filter(exam=exam)
        data = []

        for room in rooms:
            seats = SeatAllocation.objects.filter(room=room).select_related('student')
            seat_list = [{
                'seat_label': s.seat_label,
                'student_name': s.student.name,
                'reg_no': s.student.registration_number,
                'dept': s.student.department
            } for s in seats]
            data.append({
                'room': f"{room.building}-{room.room_number}",
                'capacity': room.capacity,
                'seats': seat_list
            })

        return JsonResponse({'status': 'success', 'rooms': data, 'locked': exam.seating_locked})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
