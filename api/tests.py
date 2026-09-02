from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Budget, Category, Transaction


class CategoryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", email="alice@example.com", password="password123")
        self.other_user = User.objects.create_user(username="bob", email="bob@example.com", password="password123")
        self.client.force_authenticate(user=self.user)

    def test_registration_creates_default_uncategorized_category(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "confirmPassword": "password123",
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_user = User.objects.get(username="newuser")
        category = Category.objects.get(user=new_user)
        self.assertEqual(category.name, "Uncategorized")
        self.assertTrue(category.is_default)

    def test_default_category_cannot_be_updated(self):
        default_category = Category.objects.create(user=self.user, name="Uncategorized", color="#6b7280", is_default=True)

        response = self.client.patch(
            reverse("category-detail", args=[default_category.id]),
            {"name": "Renamed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        default_category.refresh_from_db()
        self.assertEqual(default_category.name, "Uncategorized")

    def test_default_category_cannot_be_deleted(self):
        default_category = Category.objects.create(user=self.user, name="Uncategorized", color="#6b7280", is_default=True)

        response = self.client.delete(reverse("category-detail", args=[default_category.id]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Category.objects.filter(id=default_category.id).exists())

    def test_deleting_category_reassigns_transactions_to_default(self):
        default_category = Category.objects.create(user=self.user, name="Uncategorized", color="#6b7280", is_default=True)
        food_category = Category.objects.create(user=self.user, name="Food", color="#f9a8d4")
        txn = Transaction.objects.create(user=self.user, category=food_category, title="Groceries", amount="42.50", date="2026-08-01")

        response = self.client.delete(reverse("category-detail", args=[food_category.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(id=food_category.id).exists())
        txn.refresh_from_db()
        self.assertEqual(txn.category, default_category)

    def test_user_cannot_access_another_users_category(self):
        other_category = Category.objects.create(user=self.other_user, name="Secret", color="#93c5fd")

        response = self.client.get(reverse("category-detail", args=[other_category.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class TransactionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", email="alice@example.com", password="password123")
        self.other_user = User.objects.create_user(username="bob", email="bob@example.com", password="password123")
        self.client.force_authenticate(user=self.user)
        self.default_category = Category.objects.create(user=self.user, name="Uncategorized", color="#6b7280", is_default=True)
        self.food_category = Category.objects.create(user=self.user, name="Food", color="#f9a8d4")
        self.transaction = Transaction.objects.create(user=self.user, category=self.food_category, title="Groceries", amount="42.50", date="2026-08-01")

    def test_user_cannot_create_transaction_with_zero_amount(self):
        response = self.client.post(
            reverse("transaction-list"),
            {
                "category": self.food_category.id,
                "title": "Free Sample",
                "amount": "0.00",
                "date": "2026-08-01"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.filter(user=self.user, title="Free Sample").count(), 0)

    def test_user_cannot_create_transaction_with_negative_amount(self):
        response = self.client.post(
            reverse("transaction-list"),
            {
                "category": self.food_category.id,
                "title": "Invalid Transaction",
                "amount": "-10.00",
                "date": "2026-08-01"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.filter(user=self.user, title="Invalid Transaction").count(), 0)

    def test_user_cannot_create_transaction_without_category(self):
        response = self.client.post(
            reverse("transaction-list"),
            {
                "title": "No Category",
                "amount": "10.00",
                "date": "2026-08-01"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.filter(user=self.user, title="No Category").count(), 0)

    def test_user_cannot_create_transaction_without_title(self):
        response = self.client.post(
            reverse("transaction-list"),
            {
                "category": self.food_category.id,
                "amount": "10.00",
                "date": "2026-08-01"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.filter(user=self.user, amount="10.00").count(), 0)

    def test_user_cannot_create_transaction_without_date(self):
        response = self.client.post(
            reverse("transaction-list"),
            {
                "category": self.food_category.id,
                "title": "No Date",
                "amount": "10.00"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.filter(user=self.user, title="No Date").count(), 0)

    def test_user_cannot_create_transaction_without_amount(self):
        response = self.client.post(
            reverse("transaction-list"),
            {
                "category": self.food_category.id,
                "title": "No Amount",
                "date": "2026-08-01"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.filter(user=self.user, title="No Amount").count(), 0)

class BudgetTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="testuser@example.com", password="testpassword")
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(user=self.user, name="Food", color="#f9a8d4")
        self.other_user = User.objects.create_user(username="otheruser", email="otheruser@example.com", password="otherpassword")

    def test_user_can_create_budget(self):
        response = self.client.post(
            reverse("budget-list"),
            {
                "category": self.category.id,
                "month": "2026-08",
                "limit_amount": "1000.00"
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Budget.objects.filter(user=self.user, category=self.category, month="2026-08").count(), 1)

    def test_user_cannot_create_budget_without_amount(self):
        response = self.client.post(
            reverse("budget-list"),
            {
                "category": self.category.id,
                "month": "2026-08"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Budget.objects.filter(user=self.user, category=self.category, month="2026-08").count(), 0)

    def test_user_cannot_create_budget_with_zero_amount(self):
        response = self.client.post(
            reverse("budget-list"),
            {
                "category": self.category.id,
                "month": "2026-08",
                "limit_amount": "0.00"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Budget.objects.filter(user=self.user, category=self.category, month="2026-08").count(), 0)

    def test_user_cannot_create_budget_with_negative_amount(self):
        response = self.client.post(
            reverse("budget-list"),
            {
                "category": self.category.id,
                "month": "2026-08",
                "limit_amount": "-100.00"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Budget.objects.filter(user=self.user, category=self.category, month="2026-08").count(), 0)

    def test_user_cannot_create_budget_with_blank_amount(self):
        response = self.client.post(
            reverse("budget-list"),
            {
                "category": self.category.id,
                "month": "2026-08",
                "limit_amount": ""
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Budget.objects.filter(user=self.user, category=self.category, month="2026-08").count(), 0)

    def test_user_cannot_access_another_users_budget(self):
        other_category = Category.objects.create(user=self.other_user, name="Secret", color="#93c5fd")
        other_budget = Budget.objects.create(user=self.other_user, category=other_category, month="2026-08", limit_amount="500.00")

        response = self.client.get(reverse("budget-detail", args=[other_budget.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)