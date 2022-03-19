##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

from django.contrib import admin

from .models import VaultPasswordPolicy, VdxIdUser

admin.site.register(VdxIdUser)
admin.site.register(VaultPasswordPolicy)
