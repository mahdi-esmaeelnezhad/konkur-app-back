from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Role, User, UserProfile, UserRole, UserSettings
from education.models import Country, EducationSystem, Exam, ExamType, Subject
from platformcfg.models import FeatureFlag, SupportedCurrency, SupportedLocale
from social.models import Achievement, LevelDefinition
from study.models import GoalType


class Command(BaseCommand):
    help = "Seed development reference data (roles, locales, sample education)."

    @transaction.atomic
    def handle(self, *args, **options):
        roles = [
            ("student", "Student"),
            ("coach", "Coach"),
            ("parent", "Parent"),
            ("teacher", "Teacher"),
            ("school_admin", "School Administrator"),
            ("org_admin", "Organization Administrator"),
            ("community_moderator", "Community Moderator"),
            ("platform_admin", "Platform Administrator"),
        ]
        for slug, name in roles:
            Role.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "is_active": True},
            )

        SupportedLocale.objects.update_or_create(
            code="fa",
            defaults={"name": "Persian", "native_name": "فارسی", "is_rtl": True, "is_active": True},
        )
        SupportedLocale.objects.update_or_create(
            code="en",
            defaults={"name": "English", "native_name": "English", "is_rtl": False, "is_active": True},
        )
        SupportedLocale.objects.update_or_create(
            code="ar",
            defaults={"name": "Arabic", "native_name": "العربية", "is_rtl": True, "is_active": True},
        )

        for code, name in (("IRR", "Iranian Rial"), ("USD", "US Dollar"), ("EUR", "Euro")):
            SupportedCurrency.objects.update_or_create(
                code=code,
                defaults={"name": name, "is_active": True},
            )

        FeatureFlag.objects.update_or_create(
            key="social_feed",
            defaults={"enabled": True, "description": "Social activity feed"},
        )
        FeatureFlag.objects.update_or_create(
            key="coach_marketplace",
            defaults={"enabled": True, "description": "Coach marketplace"},
        )

        country, _ = Country.objects.update_or_create(
            iso_code="IR",
            defaults={"name": "Iran", "native_name": "ایران", "is_active": True},
        )
        system, _ = EducationSystem.objects.update_or_create(
            country=country,
            code="iran_secondary",
            defaults={"name": "Iranian Secondary Education", "is_active": True},
        )
        exam_type, _ = ExamType.objects.update_or_create(
            code="entrance",
            defaults={"name": "Entrance Exam", "is_active": True},
        )
        Exam.objects.update_or_create(
            code="konkur_tajrobi_1406",
            defaults={
                "name": "Konkur Experimental 1406",
                "exam_type": exam_type,
                "country": country,
                "education_system": system,
                "is_active": True,
            },
        )
        Subject.objects.update_or_create(
            code="biology",
            education_system=system,
            defaults={"name": "Biology", "is_active": True, "exam": None},
        )
        Subject.objects.update_or_create(
            code="math",
            education_system=system,
            defaults={"name": "Mathematics", "is_active": True, "exam": None},
        )

        for level, xp in ((1, 0), (2, 500), (3, 1500), (5, 5000), (10, 20000)):
            LevelDefinition.objects.update_or_create(
                level=level,
                defaults={"title": f"Level {level}", "xp_required": xp},
            )

        Achievement.objects.update_or_create(
            slug="first_session",
            defaults={
                "title": "First Session",
                "description": "Complete your first study session",
                "xp_reward": 50,
                "is_active": True,
            },
        )

        for code, name, unit in (
            ("daily_minutes", "مطالعه روزانه", "minutes"),
            ("weekly_hours", "ساعت هفتگی", "hours"),
            ("chapter_progress", "پیشرفت فصل", "percent"),
        ):
            GoalType.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": name,
                    "default_unit": unit,
                    "is_system": True,
                },
            )

        user, created = User.objects.get_or_create(
            username="demo_student",
            defaults={
                "email": "demo@konkur.local",
                "locale": "fa",
                "timezone": "Asia/Tehran",
                "account_status": "active",
            },
        )
        if created:
            user.set_password("demo-pass-123")
            user.save()

        UserProfile.objects.update_or_create(
            user=user,
            defaults={"display_name": "دانش‌آموز نمونه", "bio": "Dev seed user"},
        )
        UserSettings.objects.update_or_create(
            user=user,
            defaults={"calendar_system": "jalali"},
        )
        student_role = Role.objects.get(slug="student")
        UserRole.objects.update_or_create(
            user=user,
            role=student_role,
            defaults={"is_primary": True, "status": "active"},
        )

        self.stdout.write(self.style.SUCCESS("Dev seed complete."))
