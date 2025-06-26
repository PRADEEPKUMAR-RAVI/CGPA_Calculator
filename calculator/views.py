import random
from django.core.mail import send_mail
from .models import EmailOTP
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from datetime import timedelta
from .models import Semester, UserResult,Department,Subject
from rest_framework.decorators import api_view,permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from calculator.pagination import DynamicPageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication
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
    email = data.get("email")
    department = data.get("department")
    semester = data.get("semester")
    if not email or not semester:
        return Response({"error":"email and semester are required"}, status=status.HTTP_400_BAD_REQUEST)

    UserResult.objects.filter(email=email,semester=semester,department=department).delete() 

    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Result saved successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def user_historys(request):
    email = request.query_params.get("email")
    department = request.query_params.get("dept_id")
    if not email:
        return Response({"error":"email required"},status=status.HTTP_401_UNAUTHORIZED)
    try:
        department = Department.objects.get(id=department)
    except Department.DoesNotExist:
        return Response({"error": "Invalid department ID"}, status=status.HTTP_404_NOT_FOUND)
    
    results = UserResult.objects.filter(email=email,department=department).order_by('created_at')
    paginator = DynamicPageNumberPagination()
    paginated = paginator.paginate_queryset(results,request)
    serializer = UserSerializer(paginated, many=True)
    return Response({"history":serializer.data},status=status.HTTP_200_OK)


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminUser])
def admin_all_results(request):
    paginator = DynamicPageNumberPagination()
    paginator.page_size = 5
    results = UserResult.objects.all().order_by('-created_at')
    paginated = paginator.paginate_queryset(results, request)
    serializer = UserSerializer(paginated, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
def calculate_overall_cgpa(request):
    email = request.query_params.get("email")
    department = request.query_params.get("dept_id")
    results = UserResult.objects.filter(email=email,department=department)
    print("results for oacgpa--------------------------",results)
    total_credits = 0
    total_grade_points = 0.0

    for res in results:
        total_credits += res.total_credits
        total_grade_points += res.total_grade_points

    if total_credits == 0:
        return Response({"error": "No credits found."}, status=400)

    cgpa = round(total_grade_points / total_credits, 2)
    return Response({"cgpa": cgpa, "semester_count": results.count()})

@api_view(["DELETE"])
def delete_result(request):
    email = request.query_params.get("email")
    print("email--------",email)
    semester = request.query_params.get("semester")
    print("semester---------------",semester)
    department = request.query_params.get("department")
    print("department-------------",department)
    
    if not email or not semester or not department:
        return Response({"error": "Missing params"}, status=400)

    deleted, _ = UserResult.objects.filter(
        email=email,
        semester=semester,
        department=department
    ).delete()

    if deleted:
        return Response({"message": "Record deleted"}, status=200)
    else:
        return Response({"error": "Record not found"}, status=404)

