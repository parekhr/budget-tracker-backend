from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import Category, Transaction, Budget
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'user', 'name', 'color', 'created_at', 'updated_at']
        extra_kwargs = {
            'user': {'read_only': True}
        }

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'category', 'title', 'amount', 'date', 'additional_notes', 'created_at', 'updated_at']
        extra_kwargs = {
            'user': {'read_only': True}
        }

class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['id', 'user', 'category', 'month', 'limit_amount', 'created_at', 'updated_at']
        extra_kwargs = {
            'user': {'read_only': True}
        }

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'confirm_password']
        extra_kwargs = {
            'email': {'validators': [UniqueValidator(queryset=User.objects.all())]}
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field].required = False

    def validate(self, attrs):
        email = attrs.pop('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('No account found with that email.')
        attrs[self.username_field] = user.username
        data = super().validate(attrs)
        data['username'] = self.user.username
        return data
    
class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "Passwords do not match."})
        return data
    
class ChangeUsernameSerializer(serializers.Serializer):
    new_username = serializers.CharField(min_length=3)

    def validate_new_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

class CategoryBreakdownSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()
    color = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

class BudgetVsActualSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()
    limit_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    spent_amount = serializers.DecimalField(max_digits=10, decimal_places=2)

class SummarySerializer(serializers.Serializer):
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    budgeted = serializers.DecimalField(max_digits=10, decimal_places=2)
    remaining = serializers.DecimalField(max_digits=10, decimal_places=2)
    spend_by_category = CategoryBreakdownSerializer(many=True)
    budget_vs_actual = BudgetVsActualSerializer(many=True)
