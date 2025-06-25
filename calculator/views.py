import random
from django.core.mail import send_mail
from .models import EmailOTP
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from datetime import timedelta
from .models import Semester, UserResult,Department,Subject
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from calculator.pagination import DynamicPageNumberPagination
from .serializers import UserSerializer,SubjectSerializer,DepartmentSerializer, EmailSerializer

@api_view(["GET"])
def list_departments(request):
    departments = Department.objects.all()
    serializer = DepartmentSerializer(departments, many=True)
    return Response({"departments": serializer.data}, status=status.HTTP_200_OK)




@api_view(["POST"])
def send_otp(request):
    email = request.data.get("email")
    
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

    otp = str(random.randint(100000, 999999))
    print(f"Sending OTP to {email}: {otp}")

    
    EmailOTP.objects.create(email=email, otp=otp)

   
    send_mail(
        subject="Your CGPA Calculator OTP",
        message=f"Your OTP is {otp}",
        from_email="pradeepkumarravi.softsuave@gmail.com",
        recipient_list=[email],
    )

    return Response({"message": "OTP sent"}, status=status.HTTP_200_OK)

@swagger_auto_schema(method="post",request_body=EmailSerializer)
@api_view(["POST"])
def verify_otp(request):
    email = request.data.get("email")
    otp = request.data.get("otp")

    if not email or not otp:
        return Response({"verified": False, "error": "Email and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        record = EmailOTP.objects.filter(email=email, otp=otp).latest('created_at')
        if timezone.now() - record.created_at <= timedelta(minutes=30):
            return Response({"verified": True}, status=status.HTTP_200_OK)
        else:
            return Response({"verified": False, "error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)
    except EmailOTP.DoesNotExist:
        return Response({"verified": False, "error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)


    
@api_view(["GET"])
def subjects_by_semester_and_department(request, sem_num, dept_code):
    try:
        semester = Semester.objects.get(number=sem_num)
        department = Department.objects.get(code=dept_code)
        subjects = Subject.objects.filter(semester=semester, department=department)

        serializer = SubjectSerializer(subjects, many=True)
        return Response({"subjects": serializer.data}, status=status.HTTP_200_OK)
    except Semester.DoesNotExist:
        return Response({"error": "Semester not found"}, status=status.HTTP_404_NOT_FOUND)
    except Department.DoesNotExist:
        return Response({"error": "Department not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
def list_semesters(request):
    semesters = Semester.objects.all().order_by("number")
    data = [sem.number for sem in semesters]
    return Response({"semesters": data}, status=status.HTTP_200_OK)



@swagger_auto_schema(method="post",request_body=UserSerializer)
@api_view(["POST"])
def save_results(request):
    data = request.data
    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Result saved successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def user_historys(request):
    email = request.query_params.get("email")
    if not email:
        return Response({"error":"email required"},status=status.HTTP_401_UNAUTHORIZED)
    
    results = UserResult.objects.filter(email=email).order_by('-created_at')
    paginator = DynamicPageNumberPagination()
    paginated = paginator.paginate_queryset(results,request)
    serializer = UserSerializer(paginated, many=True)
    return Response({"history":serializer.data},status=status.HTTP_200_OK)


@api_view(["GET"])
def admin_all_results(request):
    paginator = DynamicPageNumberPagination()
    paginator.page_size = 5
    results = UserResult.objects.all().order_by('-created_at')
    paginated = paginator.paginate_queryset(results, request)
    serializer = UserSerializer(paginated, many=True)
    return paginator.get_paginated_response(serializer.data)