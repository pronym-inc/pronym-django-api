from django.contrib import admin

from .models import ApiAccount, ApiAccountMember


admin.site.register(ApiAccount)
admin.site.register(ApiAccountMember)
