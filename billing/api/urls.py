from django.urls import path

from billing.api import views

urlpatterns = [
    path("plans/", views.SubscriptionPlanListView.as_view(), name="billing-plan-list"),
    path("me/subscriptions/", views.MySubscriptionListView.as_view(), name="billing-my-subscriptions"),
    path("webhooks/stripe/", views.StripeWebhookView.as_view(), name="billing-stripe-webhook"),
]
