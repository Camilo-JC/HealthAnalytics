import logging
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = 'create', _('Crear')
        READ = 'read', _('Leer')
        UPDATE = 'update', _('Actualizar')
        DELETE = 'delete', _('Eliminar')
        LOGIN = 'login', _('Inicio de sesión')
        LOGOUT = 'logout', _('Cierre de sesión')
        EXPORT = 'export', _('Exportar')
        EXECUTE = 'execute', _('Ejecutar')
        TRAIN = 'train', _('Entrenar')
        PREDICT = 'predict', _('Predecir')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, verbose_name=_('usuario')
    )
    user_role = models.CharField(_('rol del usuario'), max_length=20, null=True, blank=True)
    action = models.CharField(_('acción'), max_length=20, choices=Action.choices)
    module = models.CharField(_('módulo'), max_length=50)
    resource_type = models.CharField(_('tipo de recurso'), max_length=50, blank=True)
    resource_id = models.CharField(_('ID del recurso'), max_length=100, blank=True, null=True)
    description = models.TextField(_('descripción'), blank=True)
    ip_address = models.GenericIPAddressField(_('dirección IP'), blank=True, null=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    success = models.BooleanField(_('éxito'), default=True)
    details = models.JSONField(_('detalles'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('registro de auditoría')
        verbose_name_plural = _('registros de auditoría')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'module']),
            models.Index(fields=['user_role']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"[{self.created_at}] {self.user} - {self.get_action_display()} / {self.module}"

    def save(self, *args, **kwargs):
        if self.user and not self.user_role:
            self.user_role = self.user.role
        super().save(*args, **kwargs)


logger = logging.getLogger('django')


def log_audit(user, action, module, resource_type='', resource_id=None,
              description='', request=None, success=True, details=None):
    try:
        ip = ''
        ua = ''
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR', '')
            ua = request.META.get('HTTP_USER_AGENT', '')
        AuditLog.objects.create(
            user=user,
            action=action,
            module=module,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            description=description,
            ip_address=ip,
            user_agent=ua,
            success=success,
            details=details,
        )
    except Exception as e:
        logger.error(f"Error logging audit: {e}")


