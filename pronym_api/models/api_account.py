"""
Model for representing API Accounts, the highest level of account organizations for APIs.
"""

from typing import Optional, TYPE_CHECKING

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Manager

if TYPE_CHECKING:  # pragma: no cover
    from pronym_api.models.api_account_member import ApiAccountMember


class ApiAccount(models.Model):
    """
    An API Account represents the highest level of organization for API Users.  An API account might correspond to
    a customer, and then they could have multiple service account members (see ApiAccountMember).
    """
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    apiaccountmember_set: 'Manager[ApiAccountMember]'

    def __str__(self) -> str:  # pragma: no cover
        return self.name

    def create_account_member(self: 'ApiAccount') -> 'ApiAccountMember':
        """Create a new member for this account."""
        # Get a unique username
        from pronym_api.models.api_account_member import ApiAccountMember
        while True:
            username = User.objects.make_random_password(
                length=ApiAccountMember.USERNAME_LENGTH)
            try:
                User.objects.get(username=username)
            except User.DoesNotExist:
                break
        user = User.objects.create(username=username)
        return ApiAccountMember.objects.create(api_account=self, user=user)

    def get_active_member(self) -> 'Optional[ApiAccountMember]':
        """Get an active member, if available, of this api account."""
        members = self.apiaccountmember_set.all()
        if members.count() == 0:
            return None
        return members[0]

    def regenerate_secret_key(self) -> str:
        """Regenerate the secret key for the account member."""
        from pronym_api.models.api_account_member import ApiAccountMember
        member = self.get_active_member()
        if member is None:
            member = self.create_account_member()
        new_password = User.objects.make_random_password(
            length=ApiAccountMember.PASSWORD_LENGTH)
        member.user.set_password(new_password)
        member.user.save()
        return new_password

    @property
    def has_active_member(self) -> bool:
        """Does this account have an active member?"""
        return self.get_active_member() is not None
