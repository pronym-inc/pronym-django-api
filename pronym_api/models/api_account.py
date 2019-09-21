from django.contrib.auth.models import User
from django.db import models

from .api_account_member import ApiAccountMember


class ApiAccount(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_sweetrelish_enabled = models.BooleanField(default=False)
    sweetrelish_email = models.EmailField(null=True, blank=True)

    def __str__(self):
        return self.name

    def create_account_member(self):
        # Get a unique username
        while True:
            username = User.objects.make_random_password(
                length=ApiAccountMember.USERNAME_LENGTH)
            try:
                User.objects.get(username=username)
            except User.DoesNotExist:
                break
        user = User.objects.create(username=username)
        return ApiAccountMember.objects.create(api_account=self, user=user)

    def get_active_member(self):
        members = self.members.order_by('-id')
        if members.count() == 0:
            return None
        return members[0]

    def regenerate_secret_key(self):
        member = self.get_active_member()
        if member is None:
            member = self.create_account_member()
        new_password = User.objects.make_random_password(
            length=ApiAccountMember.PASSWORD_LENGTH)
        member.user.set_password(new_password)
        member.user.save()
        return new_password

    @property
    def has_active_member(self):
        return self.get_active_member() is not None
