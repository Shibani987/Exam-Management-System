from django.db import models

# STEP 1: Exam
class Exam(models.Model):
    SESSION_CHOICES = [
        ('firstHalf', 'First Half (10:00 AM - 1:00 PM)'),
        ('secondHalf', 'Second Half (2:00 PM - 5:00 PM)'),
    ]

    name = models.CharField(max_length=200)
    date = models.DateField()
    session = models.CharField(max_length=20, choices=SESSION_CHOICES)
    seating_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.session}"



# STEP 2: Department + Paper
class DepartmentExam(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='departments')
    department = models.CharField(max_length=100)
    paper_name = models.CharField(max_length=200)
    paper_code = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.department} ({self.paper_name})"


# STEP 3: Room Setup
class Room(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='rooms')
    building = models.CharField(max_length=100)
    room_number = models.CharField(max_length=50)
    capacity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.building} - {self.room_number}"

#STEP 4: UPload styudent list
class Student(models.Model):
    exam = models.ForeignKey('Exam', on_delete=models.CASCADE, related_name='students')
    department = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=100)
    name = models.CharField(max_length=200)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.roll_number} - {self.name}"

#step 5: seat allotment
class SeatAllocation(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='allocations')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    session = models.CharField(max_length=20)
    row = models.CharField(max_length=5)
    column = models.IntegerField()
    seat_label = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.registration_number} -> {self.room.room_number} ({self.seat_label})"
