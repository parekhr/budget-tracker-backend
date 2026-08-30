from django.db.models.aggregates import Sum
from django.db import transaction
from rest_framework import viewsets, generics
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import User
from .models import Category, Transaction, Budget
from .serializers import CategorySerializer, ChangePasswordSerializer, ChangeUsernameSerializer, EmailTokenObtainPairSerializer, RegistrationSerializer, SummarySerializer, TransactionSerializer, BudgetSerializer, TrendPointSerializer
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from .serializers import PasswordResetRequestSerializer, PasswordResetConfirmSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.is_default:
            raise PermissionDenied("Default category cannot be updated.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.is_default:
            raise PermissionDenied("Default category cannot be deleted.")
        default_category = Category.objects.get(user=self.request.user, is_default=True)
        with transaction.atomic():
            instance.transactions.update(category=default_category)
            instance.delete()

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        Category.objects.create(user=user, name="Uncategorized", color="#6b7280", is_default=True)

        refresh = RefreshToken.for_user(user)
        return Response({
            'username': user.username,
            'email': user.email,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=201) 
        
class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        #validate incoming data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data['email']).first()

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = PasswordResetTokenGenerator().make_token(user)
            reset_url = f"http://localhost:5173/reset-password/{uid}/{token}"
            send_mail(
                'Password Reset Request',
                f'Click the link to reset your password: {reset_url}',
                'from@example.com',
                [user.email],
                fail_silently=False,
            )
        return Response({'message': 'If an account with that email exists, a password reset link has been sent.'})

class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid = force_str(urlsafe_base64_decode(serializer.validated_data['uid']))
        user = User.objects.filter(pk=uid).first()

        if user is None:
            return Response({'detail': 'Invalid reset link.'}, status=400)

        token = serializer.validated_data['token']
        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({'detail': 'Invalid reset link.'}, status=400)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Password has been reset successfully.'})

class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data['current_password']):
            return Response({'detail': 'Current password is incorrect.'}, status=400)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Password changed successfully.'})

class ChangeUsernameView(generics.GenericAPIView):
    serializer_class = ChangeUsernameSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_username = serializer.validated_data['new_username']
        request.user.username = new_username
        request.user.save()
        return Response({'detail': 'Username changed successfully.', 'username': new_username})

class SummaryView(generics.GenericAPIView):
    serializer_class = SummarySerializer

    def get(self, request, *args, **kwargs):
        month = request.query_params.get('month')
        user = request.user

        transactions = Transaction.objects.filter(user=request.user, date__startswith=month)
        budgets = Budget.objects.filter(user=request.user, month=month)

        total_spent = transactions.aggregate(total=Sum('amount'))['total'] or 0
        budgeted = budgets.aggregate(total=Sum('limit_amount'))['total'] or 0
        remaining = budgeted - total_spent

        grouped = transactions.values('category', 'category__name', 'category__color').annotate(total=Sum('amount'))

        data = {
            "total_spent": total_spent,
            "budgeted": budgeted,
            "remaining": remaining,
            "spend_by_category": [
                {"category_id": g['category'], "category_name": g['category__name'], "color": g['category__color'], "amount": g['total']} for g in grouped
            ],
            "budget_vs_actual": [
                {"category_id": b.category_id, "category_name": b.category.name, "limit_amount": b.limit_amount, "spent_amount": transactions.filter(category_id=b.category_id).aggregate(total=Sum('amount'))['total'] or 0} for b in budgets
            ]
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data)

class UsernameView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        return Response({'username': request.user.username})

class TrendsView(generics.GenericAPIView):
    serializer_class = TrendPointSerializer

    def get(self, request, *args, **kwargs):
        months = int(request.query_params.get('months'))
        end_month = request.query_params.get('endMonth')
        end_year, end_month_num = map(int, end_month.split('-'))
        end_total_months = end_year * 12 + (end_month_num - 1)

        points = []
        for i in range(months - 1, -1, -1):
            total_months = end_total_months - i
            year, month_index = divmod(total_months, 12)
            period = f"{year}-{month_index + 1:02d}"

            total_spent = Transaction.objects.filter(
                user=request.user, date__startswith=period
            ).aggregate(total=Sum('amount'))['total'] or 0

            points.append({'period': period, 'total_spent': total_spent})

        serializer = self.get_serializer(points, many=True)
        return Response(serializer.data)