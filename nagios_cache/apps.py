from __future__ import unicode_literals

from django.apps import AppConfig
from django.conf import settings

from django.core.checks import Error, Warning, register

DEFAULT_CONFIG = {
    'NAGIOS_CACHE_URL': None,
    'NAGIOS_CACHE_USER': None,
    'NAGIOS_CACHE_PASSWORD': None,
    'NAGIOS_CACHE_AUTOCLEAN': False,
    'NAGIOS_CACHE_AUTOCLEAN_DAYS': 1,
}


class NagiosCacheConfig(AppConfig):
    name = 'nagios_cache'

    def ready(self):
        for k, v in DEFAULT_CONFIG.iteritems():
            if not hasattr(settings, k):
                setattr(settings, k, v)


@register()
def config_validation(app_configs, **kwargs):
    errors = []
    if bool(settings.NAGIOS_CACHE_USER) ^ bool(settings.NAGIOS_CACHE_PASSWORD):
        errors.append(Warning('You should either define both or non of settings.NAGIOS_CACHE_USER and '
                              'settings.NAGIOS_CACHE_PASSWORD. Authentication at the Nagios/Icinga host '
                              'is disable. This is properly not what you want.',
                              id='nagios_cache.W001'))
    if not settings.NAGIOS_CACHE_URL:
        errors.append(Error('You must define settings.NAGIOS_CACHE_URL', id='nagios_cache.E001'))
    if settings.NAGIOS_CACHE_AUTOCLEAN and not type(settings.NAGIOS_CACHE_AUTOCLEAN_DAYS) == int:
        errors.append(Error('settings.NAGIOS_CACHE_AUTOCLEAN_DAYS must be an integer', id='nagios_cache.E002'))

    return errors

