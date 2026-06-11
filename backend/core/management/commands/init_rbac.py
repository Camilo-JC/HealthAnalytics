from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialize RBAC roles for existing users without a role'

    def handle(self, *args, **options):
        updated = User.objects.filter(role__isnull=True).update(role='analyst')
        updated += User.objects.filter(role='').update(role='analyst')
        self.stdout.write(self.style.SUCCESS(f'Updated {updated} users with default role'))
        counts = {}
        for role, label in User.Role.choices:
            cnt = User.objects.filter(role=role).count()
            counts[role] = cnt
            self.stdout.write(f'  {label}: {cnt} users')
        return f"RBAC initialized: {counts}"
