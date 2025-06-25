from rest_framework import serializers
from .models import UserResult,Semester,Subject,Department,EmailOTP


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserResult
        fields = '__all__'


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailOTP
        fields = ["email"]


class SubjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subject
        fields = ["code", "name", "credit"]

class SemesterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Semester
        fields = ["number"]

class DepartmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Department
        fields = ['id', 'name', 'code']  
