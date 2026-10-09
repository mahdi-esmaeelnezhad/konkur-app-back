from django.urls import path

from messaging.api import views

urlpatterns = [
    path("conversations/", views.ConversationListCreateView.as_view(), name="conversation-list"),
    path(
        "conversations/<uuid:conversation_id>/messages/",
        views.ConversationMessageListCreateView.as_view(),
        name="conversation-messages",
    ),
    path(
        "conversations/<uuid:conversation_id>/read/",
        views.ConversationMarkReadView.as_view(),
        name="conversation-mark-read",
    ),
    path("notifications/", views.NotificationListView.as_view(), name="notification-list"),
    path(
        "notifications/unread-count/",
        views.NotificationUnreadCountView.as_view(),
        name="notification-unread-count",
    ),
    path(
        "notifications/read-all/",
        views.NotificationMarkAllReadView.as_view(),
        name="notification-read-all",
    ),
    path(
        "notifications/<uuid:pk>/read/",
        views.NotificationMarkReadView.as_view(),
        name="notification-read",
    ),
    path(
        "notification-preferences/",
        views.NotificationPreferencesView.as_view(),
        name="notification-preferences",
    ),
]
