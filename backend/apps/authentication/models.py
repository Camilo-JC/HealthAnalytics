from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Administrador')
        DOCTOR = 'doctor', _('Médico')
        ANALYST = 'analyst', _('Analista')

    class DocumentType(models.TextChoices):
        CC = 'cc', _('Cédula de Ciudadanía')
        CE = 'ce', _('Cédula de Extranjería')
        PASSPORT = 'passport', _('Pasaporte')
        NIT = 'nit', _('NIT')

    username = None
    email = models.EmailField(_('correo electrónico'), unique=True)
    full_name = models.CharField(_('nombre completo'), max_length=255)
    document_type = models.CharField(
        _('tipo de documento'), max_length=20,
        choices=DocumentType.choices, default=DocumentType.CC
    )
    document_id = models.CharField(
        _('número de documento'), max_length=50, unique=True, null=True, blank=True
    )
    phone = models.CharField(_('teléfono'), max_length=20, blank=True)
    role = models.CharField(
        _('rol'), max_length=20, choices=Role.choices, default=Role.ANALYST
    )
    avatar = models.ImageField(
        _('avatar'), upload_to='avatars/', null=True, blank=True
    )
    is_active = models.BooleanField(_('activo'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'role']

    class Meta:
        verbose_name = _('usuario')
        verbose_name_plural = _('usuarios')
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"
