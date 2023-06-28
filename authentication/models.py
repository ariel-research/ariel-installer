from __future__ import unicode_literals

__author__ = 'David Baum'

import logging, uuid

from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin)
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from guardian.mixins import GuardianUserMixin

from safedelete.models import SafeDeleteModel

from abstract.models import AIAbstractDateHistoryModel

logger = logging.getLogger(__name__)


class AIUserManager(BaseUserManager):
    """Custom manager for IAUser."""

    def _create_user(self, email, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Create and save an EmailUser with the given email and password.

        :param str email: user email
        :param str password: user password
        :param bool is_staff: whether user staff or not
        :param bool is_superuser: whether user admin or not
        :return custom_user.models.EmailUser user: user
        :raise ValueError: email is not set
        """
        now = timezone.now()
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        is_active = extra_fields.pop("is_active", True)
        user = self.model(email=email, is_staff=is_staff, is_active=is_active,
                          is_superuser=is_superuser, last_login=None,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save an IAUser with the given email and password.

        :param str email: user email
        :param str password: user password
        :return custom_user.models.EmailUser user: regular user
        """
        is_staff = extra_fields.pop("is_staff", False)
        return self._create_user(email, password, is_staff, False,
                                 **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save an EmailUser with the given email and password.

        :param str email: user email
        :param str password: user password
        :return custom_user.models.EmailUser user: admin user
        """
        return self._create_user(email, password, True, True,
                                 **extra_fields)


class AbstractAIUser(AbstractBaseUser, AIAbstractDateHistoryModel, PermissionsMixin, GuardianUserMixin,
                     SafeDeleteModel):
    """
    Abstract User with the same behaviour as Django's default User.

    AbstractIAUser does not have username field. Uses email as the
    USERNAME_FIELD for authentication.
    Use this if you need to extend IAUser.
    Inherits from both the AbstractBaseUser and PermissionMixin.
    The following attributes are inherited from the superclasses:
        * password
        * last_login
        * is_superuser
    """
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False, verbose_name=_('Unique UUID hash'))
    username = models.CharField(_('username'), max_length=255, unique=False, null=True, default=None)
    email = models.EmailField(_('email address'), max_length=255,
                              unique=True, db_index=True)
    full_name = models.CharField(_('Full name'), max_length=100, blank=True, null=True, default=None)
    company = models.CharField(_('Company'), max_length=100, blank=True, null=True, default=None)
    is_staff = models.BooleanField(
        _('staff status'), default=False, help_text=_(
            'Designates whether the user can log into this admin site.'))
    is_active = models.BooleanField(_('active'), default=True, help_text=_(
        'Designates whether this user should be treated as '
        'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    is_pending_deletion = models.BooleanField(_('pending deletion'), default=False,
                                              help_text=_(
                                                  'Designates whether the user has requested full account deletion'))
    job_title = models.CharField(_('Job title'), max_length=100, blank=True, null=True, default=None)
    referral = models.CharField(_('How did you hear about us?'), max_length=255, blank=True, null=True, default=None)
    description = models.TextField(verbose_name=_("Description"), blank=True, null=True,
                                   default=None)
    objects = AIUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        abstract = True


class AIUser(AbstractAIUser):
    class Meta(AbstractAIUser.Meta):
        swappable = 'AUTH_USER_MODEL'
