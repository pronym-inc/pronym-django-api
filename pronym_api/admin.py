from django.contrib import admin

from .models import ApiAccount, ApiAccountMember, ApiPermission


admin.site.register(ApiAccount)
admin.site.register(ApiAccountMember)
admin.site.register(ApiPermission)
