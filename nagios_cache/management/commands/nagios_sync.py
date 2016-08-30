# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from nagios_cache.models import NagiosServiceStatus, NagiosHostStatus, NagiosHostgroup, NagiosServicegroup


class Command(BaseCommand):
    help = 'Sync Nagios with the database. If no parameter is given all data will be synced'

    PROGRESS_LOG_TIME = 10

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        """
        Optionally you may import a single hostgroup or servicegroup definition.
        Note that importing a hostgroup will NOT import the associated services. (But importing a servicegroup will)
        """
        parser.add_argument('--hostgroups', nargs='*', type=str, help='Only sync the given hostgroups')
        parser.add_argument('--servicegroups', nargs='*', type=str, help='Only sync the given servicegroups')
        parser.add_argument('--sync-hosts', action='store_true', help='Sync hosts')
        parser.add_argument('--sync-services', action='store_true', help='Sync services')
        parser.add_argument('--sync-hostgroups', action='store_true', help='Sync hostgroups')
        parser.add_argument('--sync-servicegroups', action='store_true', help='Sync servicegroups')
        parser.add_argument('--clean', action='store_true', help='Cleanup database entries that are old than 1 day')

    @transaction.atomic
    def handle(self, *args, **options):
        """
        When talking about ordering of the import you should ALWAYS:

        hosts before servicegroups
        hosts before hostgroups
        services before servicegroups
        """
        # We have to save the current time for later cleanup
        current_time = timezone.now()
        if options['clean']:
            NagiosHostStatus.clean_old()
            NagiosHostgroup.clean_old()
            NagiosServiceStatus.clean_old()
            NagiosServicegroup.clean_old()
        if options['sync_hosts']:
            NagiosHostStatus.import_all(current_time)
        if options['sync_hostgroups']:
            NagiosHostgroup.import_all(current_time)
        if options['sync_services']:
            NagiosServiceStatus.import_all(current_time)
        if options['sync_servicegroups']:
            NagiosServicegroup.import_all(current_time)
        # Check if there is a hostgroup given
        if options['hostgroups']:
            for i in options['hostgroups']:
                NagiosHostgroup.import_single(current_time, i)
        # Check if there is a servicegroup given
        if options['servicegroups']:
            for i in options['servicegroups']:
                NagiosServicegroup.import_single(current_time, i)
        # If nothing is given -> sync everything
        if (not options['sync_hosts']
            and not options['sync_hostgroups']
            and not options['sync_services']
            and not options['sync_servicegroups']
            and not options['hostgroups']
            and not options['servicegroups']
            and not options['clean']
            ):
            NagiosHostStatus.import_all(current_time)
            NagiosHostgroup.import_all(current_time)
            NagiosServiceStatus.import_all(current_time)
            NagiosServicegroup.import_all(current_time)
