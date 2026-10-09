from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import Role, User, UserRole
from coaching.models import CoachNote, CoachProfile, CoachStudentRelationship
from common.access import (
    coach_can_access_student,
    coach_notes_for_student_viewer,
    coach_notes_queryset_for_user,
    org_admin_can_access,
    parent_can_view_child,
    teacher_can_access_class,
    visible_posts_queryset_for,
)
from org.models import (
    Organization,
    OrganizationMembership,
    ParentChildRelationship,
    School,
    TeacherClassAssignment,
    TeacherProfile,
)
from social.models import Post, PostVisibility
from study.models import StudySession


class MultiRoleAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="multi",
            email="multi@test.local",
            password="x",
            account_status="active",
        )
        self.student = Role.objects.create(slug="student", name="Student")
        self.coach = Role.objects.create(slug="coach", name="Coach")
        self.parent = Role.objects.create(slug="parent", name="Parent")

    def test_user_can_hold_multiple_roles(self):
        UserRole.objects.create(user=self.user, role=self.student, is_primary=True)
        UserRole.objects.create(user=self.user, role=self.coach)
        UserRole.objects.create(user=self.user, role=self.parent)
        self.assertEqual(self.user.user_roles.filter(status="active").count(), 3)


class ParentChildAuthTests(TestCase):
    def setUp(self):
        self.parent = User.objects.create_user(
            username="parent1",
            email="p1@test.local",
            password="x",
            account_status="active",
        )
        self.child = User.objects.create_user(
            username="child1",
            email="c1@test.local",
            password="x",
            account_status="active",
        )
        self.other = User.objects.create_user(
            username="child2",
            email="c2@test.local",
            password="x",
            account_status="active",
        )
        self.rel = ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            status="active",
        )

    def test_parent_can_access_authorized_child(self):
        self.assertTrue(parent_can_view_child(self.parent.id, self.child.id))

    def test_parent_denied_unrelated_child(self):
        self.assertFalse(parent_can_view_child(self.parent.id, self.other.id))

    def test_revoked_relationship_denies_access(self):
        self.rel.status = "revoked"
        self.rel.save(update_fields=["status"])
        self.assertFalse(parent_can_view_child(self.parent.id, self.child.id))


class CoachStudentAuthTests(TestCase):
    def setUp(self):
        self.coach_user = User.objects.create_user(
            username="coach1",
            email="coach1@test.local",
            password="x",
            account_status="active",
        )
        self.other_coach = User.objects.create_user(
            username="coach2",
            email="coach2@test.local",
            password="x",
            account_status="active",
        )
        self.student = User.objects.create_user(
            username="stu1",
            email="stu1@test.local",
            password="x",
            account_status="active",
        )
        self.other_student = User.objects.create_user(
            username="stu2",
            email="stu2@test.local",
            password="x",
            account_status="active",
        )
        self.profile = CoachProfile.objects.create(user=self.coach_user)
        self.other_profile = CoachProfile.objects.create(user=self.other_coach)
        CoachStudentRelationship.objects.create(
            coach=self.profile,
            student=self.student,
            status="active",
        )
        self.note = CoachNote.objects.create(
            coach=self.profile,
            student=self.student,
            body="private",
        )

    def test_student_can_have_multiple_coaches(self):
        CoachStudentRelationship.objects.create(
            coach=self.other_profile,
            student=self.student,
            status="active",
        )
        self.assertEqual(
            CoachStudentRelationship.objects.filter(
                student=self.student, status="active"
            ).count(),
            2,
        )

    def test_coach_denied_unrelated_student(self):
        self.assertFalse(coach_can_access_student(self.coach_user, self.other_student.id))

    def test_coach_can_access_authorized_student(self):
        self.assertTrue(coach_can_access_student(self.coach_user, self.student.id))

    def test_ended_relationship_denies_access(self):
        CoachStudentRelationship.objects.filter(
            coach=self.profile, student=self.student
        ).update(status="ended", ended_at=timezone.now())
        self.assertFalse(coach_can_access_student(self.coach_user, self.student.id))

    def test_coach_cannot_read_other_coach_notes(self):
        qs = coach_notes_queryset_for_user(self.other_coach)
        self.assertFalse(qs.filter(pk=self.note.pk).exists())

    def test_student_cannot_read_coach_notes(self):
        self.assertFalse(coach_notes_for_student_viewer(self.student).exists())

    def test_duplicate_active_relationship_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CoachStudentRelationship.objects.create(
                    coach=self.profile,
                    student=self.student,
                    status="active",
                )


class OrgTenantAuthTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="orgadmin",
            email="oa@test.local",
            password="x",
            account_status="active",
        )
        self.outsider = User.objects.create_user(
            username="outsider",
            email="out@test.local",
            password="x",
            account_status="active",
        )
        self.org_a = Organization.objects.create(name="Org A", slug="org-a")
        self.org_b = Organization.objects.create(name="Org B", slug="org-b")
        OrganizationMembership.objects.create(
            organization=self.org_a,
            user=self.admin,
            role="admin",
            status="active",
        )

    def test_org_admin_denied_other_organization(self):
        self.assertFalse(org_admin_can_access(self.admin, self.org_b.id))

    def test_org_admin_allowed_own_organization(self):
        self.assertTrue(org_admin_can_access(self.admin, self.org_a.id))

    def test_left_membership_denies_access(self):
        OrganizationMembership.objects.filter(
            organization=self.org_a, user=self.admin
        ).update(status="left", ended_at=timezone.now())
        self.assertFalse(org_admin_can_access(self.admin, self.org_a.id))


class TeacherClassAuthTests(TestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username="teacher1",
            email="t1@test.local",
            password="x",
            account_status="active",
        )
        self.other_teacher = User.objects.create_user(
            username="teacher2",
            email="t2@test.local",
            password="x",
            account_status="active",
        )
        self.org = Organization.objects.create(name="School Org", slug="school-org")
        self.school = School.objects.create(
            organization=self.org, name="School 1", slug="school-1"
        )
        self.tp = TeacherProfile.objects.create(user=self.teacher_user, school=self.school)
        self.other_tp = TeacherProfile.objects.create(
            user=self.other_teacher, school=self.school
        )
        self.assignment = TeacherClassAssignment.objects.create(
            teacher=self.tp,
            school=self.school,
            class_name="12A",
            subject_name="Biology",
            academic_year="1405-1406",
        )

    def test_teacher_denied_unauthorized_class(self):
        self.assertFalse(teacher_can_access_class(self.other_teacher, self.assignment.id))

    def test_teacher_allowed_own_class(self):
        self.assertTrue(teacher_can_access_class(self.teacher_user, self.assignment.id))


class SocialPrivacyTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="author",
            email="a@test.local",
            password="x",
            account_status="active",
        )
        self.viewer = User.objects.create_user(
            username="viewer",
            email="v@test.local",
            password="x",
            account_status="active",
        )
        self.private = Post.objects.create(
            author=self.author,
            body="secret",
            visibility=PostVisibility.PRIVATE,
        )
        self.public = Post.objects.create(
            author=self.author,
            body="hello",
            visibility=PostVisibility.PUBLIC,
        )

    def test_private_posts_hidden_from_unauthorized_feed(self):
        qs = visible_posts_queryset_for(self.viewer)
        self.assertFalse(qs.filter(pk=self.private.pk).exists())
        self.assertTrue(qs.filter(pk=self.public.pk).exists())


class StudySessionConcurrencyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="sess",
            email="s@test.local",
            password="x",
            account_status="active",
        )

    def test_one_live_session_per_user(self):
        StudySession.objects.create(
            user=self.user,
            status="active",
            started_at=timezone.now(),
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                StudySession.objects.create(
                    user=self.user,
                    status="paused",
                    started_at=timezone.now(),
                )
