from django.db import models


class EmailOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.otp}"
    
class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name


class Semester(models.Model):
    number = models.IntegerField()

    def __str__(self):
        return f"Semester {self.number}"
    

class Subject(models.Model):
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    credit = models.IntegerField()
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='subjects',null=False)

    def __str__(self):
        return f"{self.code} - {self.name}"


class UserResult(models.Model):
    email = models.EmailField()
    cgpa = models.FloatField()
    semester = models.IntegerField(default=1)
    department = models.ForeignKey(Department, on_delete=models.CASCADE,null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - CGPA: {self.cgpa} - Dept: {self.department.code}"
    
