# -*- coding: utf-8 -*-





from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction

from nagios_cache.models import NagiosServiceStatus, NagiosHostStatus, NagiosHostgroup, NagiosServicegroup
from nagios_cache.apps import DEFAULT_CONFIG


class Command(BaseCommand):

    TD_DAYS_DEFAULT = "(default)" if settings.NAGIOS_CACHE_CLEANCOMMAND_DAYS == DEFAULT_CONFIG['NAGIOS_CACHE_CLEANCOMMAND_DAYS'] else ""
    TD_HOURS_DEFAULT = "(default)" if settings.NAGIOS_CACHE_CLEANCOMMAND_HOURS == DEFAULT_CONFIG['NAGIOS_CACHE_CLEANCOMMAND_HOURS'] else ""

    help = """
    Clean Nagios cache in the database. You can adjust the age of the data in your settings.
    Currently the settings are defined via your settings or default values:

    NAGIOS_CACHE_CLEANCOMMAND_DAYS = %s %s
    NAGIOS_CACHE_CLEANCOMMAND_HOURS = %s %s

    """ % (settings.NAGIOS_CACHE_CLEANCOMMAND_DAYS, TD_DAYS_DEFAULT, settings.NAGIOS_CACHE_CLEANCOMMAND_HOURS, TD_HOURS_DEFAULT)

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    @transaction.atomic
    def handle(self, *args, **options):
        NagiosHostStatus.clean_old(days=settings.NAGIOS_CACHE_CLEANCOMMAND_DAYS, hours=settings.NAGIOS_CACHE_CLEANCOMMAND_HOURS)
        NagiosHostgroup.clean_old(days=settings.NAGIOS_CACHE_CLEANCOMMAND_DAYS, hours=settings.NAGIOS_CACHE_CLEANCOMMAND_HOURS)
        NagiosServiceStatus.clean_old(days=settings.NAGIOS_CACHE_CLEANCOMMAND_DAYS, hours=settings.NAGIOS_CACHE_CLEANCOMMAND_HOURS)
        NagiosServicegroup.clean_old(days=settings.NAGIOS_CACHE_CLEANCOMMAND_DAYS, hours=settings.NAGIOS_CACHE_CLEANCOMMAND_HOURS)
