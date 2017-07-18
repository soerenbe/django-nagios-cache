

import parsedatetime
import pytz
import logging
import requests

from datetime import datetime, timedelta
from django.db import models
from django.utils import timezone
from django.conf import settings

log = logging.getLogger(__name__)


class NagiosImportable(models.Model):
    """
    This is the generic class that provides basic class methods for downloading the JSON files
    from Nagios/Icinga and convert them to Django objects.
    """
    # We use this custom field to store the last sync. It can not be 'auto_now' because we want
    # to delete items bases on this value.
    # TODO: Maybe the timestamp is the same in the complete transaction?
    last_database_update = models.DateTimeField(auto_now_add=True)

    @classmethod
    def clean_old(cls, days=0, hours=0):
        query = cls.objects.filter(last_database_update__lt=timezone.now()-timedelta(days=days)-timedelta(hours=hours))
        log.debug('Removing %s old entries for %s that are older than %s days and %s hours' % (query.count(), cls.__name__, days, hours))
        query.delete()


    @classmethod
    def run_autoclean(cls):
        if settings.NAGIOS_CACHE_AUTOCLEAN:
            cls.clean_old(days=settings.NAGIOS_CACHE_AUTOCLEAN_DAYS)

    @staticmethod
    def get_nagios_url(suffix):
        """
        This will return the URL that is used to download the json file from Icinga/Nagios
        """
        return '%s?%s' % (settings.NAGIOS_CACHE_URL, suffix)

    @classmethod
    def get_json_from_url(cls, suffix):
        """
        This method will download the JSON data from Icinga/Nagios
        """
        auth = ()
        used_url = cls.get_nagios_url(suffix)
        if hasattr(settings, 'NAGIOS_CACHE_USER') and hasattr(settings, 'NAGIOS_CACHE_PASSWORD'):
            # With both is given, we use it for authentication
            auth = (settings.NAGIOS_CACHE_USER, settings.NAGIOS_CACHE_PASSWORD)
        elif hasattr(settings, 'NAGIOS_CACHE_USER') or hasattr(settings, 'NAGIOS_CACHE_PASSWORD'):
            # Only specifing the user or password is a warning. From here we do NOT use authentication
            log.warn('Only NAGIOS_CACHE_USER or NAGIOS_CACHE_PASSWORD is set. Ignore authentication')
        else:
            auth = ()
        log.debug('Fetching data from %s' % used_url)
        t = timezone.now()
        r = requests.get(used_url, auth=auth)
        log.debug('Download took %s seconds' % (timezone.now()-t))
        return r.json()

    @classmethod
    def nagios2object(cls, nagios_dict, current_time):
        # Map the dict to the class attributes
        obj = cls(**nagios_dict)
        # Fix fields that does not match the datatype
        obj.attempts, obj.attempts_of = list(map(int, obj.attempts.split('/')))
        # parse the duration field and assign it to the duration field.
        # Unfortunatly the nagios syntax is kinda strange...
        cal = parsedatetime.Calendar()
        # We need to do this to make the nagios time timezone aware
        future_time, _ = cal.parse(obj.duration)
        future_time = pytz.utc.localize(timezone.datetime(*future_time[:6]))
        obj.duration = future_time - current_time
        last_check, _ = cal.parse(obj.last_check)
        obj.last_check = pytz.utc.localize(timezone.datetime(*last_check[:6]))
        # Map the states
        obj.state_type = NagiosServiceStatus.state_type_from_nagios(obj.state_type)
        obj.status = NagiosServiceStatus.status_from_nagios(obj.status)
        # Set the last update time
        obj.last_database_update = current_time
        return obj

    class Meta:
        abstract = True


class NagiosStatus(NagiosImportable):
    """
    This is a abstract class. This is possible because Host and Service are very similar.
    For Hostgroups and Servicegroups there will be a own implementation.
    """

    STATE_TYPE_HARD = 1
    STATE_TYPE_SOFT = 2

    STATUS_OK = 1
    STATUS_UP = 2
    STATUS_DOWN = 3
    STATUS_WARNING = 4
    STATUS_CRITICAL = 5
    STATUS_UNKNOWN = 6
    STATUS_PENDING = 7
    STATUS_UNREACHABLE = 8

    STATE_TYPE = [
        [STATE_TYPE_HARD, 'HARD'],
        [STATE_TYPE_SOFT, 'SOFT'],
    ]

    STATUS = [
        [STATUS_OK, 'OK'],
        [STATUS_UP, 'UP'],
        [STATUS_DOWN, 'DOWN'],
        [STATUS_WARNING, 'WARNING'],
        [STATUS_CRITICAL, 'CRITICAL'],
        [STATUS_UNKNOWN, 'UNKNOWN'],
        [STATUS_PENDING, 'PENDING'],
        [STATUS_UNREACHABLE, 'UNREACHABLE'],
    ]

    action_url = models.URLField(blank=True, null=True)
    active_checks_enabled = models.BooleanField()
    attempts = models.SmallIntegerField()
    attempts_of = models.SmallIntegerField()
    duration = models.DurationField()
    has_been_acknowledged = models.BooleanField()
    host_display_name = models.CharField(max_length=200)
    host_name = models.CharField(max_length=200)
    in_scheduled_downtime = models.BooleanField()
    is_flapping = models.BooleanField()
    last_check = models.DateTimeField()
    notes_url = models.URLField(blank=True, null=True)
    notifications_enabled = models.BooleanField()
    passive_checks_enabled = models.BooleanField()
    state_type = models.SmallIntegerField(choices=STATE_TYPE)
    status = models.SmallIntegerField(choices=STATUS)
    status_information = models.TextField()


    class Meta:
        abstract = True

    def __unicode__(self):
        return self.host_display_name

    @staticmethod
    def state_type_from_nagios(s):
        for i in NagiosStatus.STATE_TYPE:
            if i[1] == s:
                return i[0]
        raise Exception('Unknown NagiosStatus.state_type: %s' % s)

    @staticmethod
    def status_from_nagios(s):
        for i in NagiosStatus.STATUS:
            if i[1] == s:
                return i[0]
        raise Exception('Unknown NagiosStatus.status: %s' % s)


class NagiosHostStatus(NagiosStatus):

    suffix = 'style=hostdetail&jsonoutput'

    class Meta:
        unique_together = [['host_name']]

    @staticmethod
    def import_all(current_time):
        NagiosHostStatus.run_autoclean()
        items = NagiosHostStatus.get_json_from_url(NagiosHostStatus.suffix)
        nagios_list = items['status']['host_status']
        log.info('Importing %s NagiosHostStatus from %s' % (len(nagios_list), NagiosHostStatus.get_nagios_url(NagiosHostStatus.suffix)))
        t = timezone.now()
        for current_status in nagios_list:
            # Create a database object
            obj = NagiosHostStatus.nagios2object(current_status, current_time)
            # If the object already exists, assign the PK to the new object.
            if NagiosHostStatus.objects.filter(host_name=obj.host_name).exists():
                obj.id = NagiosHostStatus.objects.get(host_name=obj.host_name).id
            obj.save()
        log.debug('Import took %s seconds' % (timezone.now() - t))


class NagiosServiceStatus(NagiosStatus):
    service_description = models.CharField(max_length=200)
    service_display_name = models.CharField(max_length=200)
    host = models.ForeignKey(NagiosHostStatus)

    suffix = 'jsonoutput'

    class Meta:
        unique_together = [['host', 'host_name', 'service_description']]

    def __unicode__(self):
        return "%s | %s" % (self.host.host_display_name, self.service_display_name)

    @staticmethod
    def import_from_url(current_time, url):
        NagiosServiceStatus.run_autoclean()
        items = NagiosServiceStatus.get_json_from_url(url)
        nagios_list = items['status']['service_status']
        log.info('Importing %s NagiosServiceStatus from %s' % (len(nagios_list), NagiosServiceStatus.get_nagios_url(url)))
        t = timezone.now()
        for current_status in nagios_list:
            # Create a database object
            obj = NagiosServiceStatus.nagios2object(current_status, current_time)
            # Lookup the foreign key for the host
            obj.host = NagiosHostStatus.objects.get(host_name=obj.host_name)
            if NagiosServiceStatus.objects.filter(host_name=obj.host_name, service_description=obj.service_description).exists():
                # If the object already exists, assign the PK to the new object.
                obj.id = NagiosServiceStatus.objects.get(host_name=obj.host_name, service_description=obj.service_description).id
            obj.save()
        log.debug('Import took %s seconds' % (timezone.now() - t))

    @staticmethod
    def import_all(current_time):
        NagiosServiceStatus.import_from_url(current_time, NagiosServiceStatus.suffix)


class NagiosHostgroup(NagiosImportable):
    name = models.CharField(max_length=200)
    hosts = models.ManyToManyField(NagiosHostStatus)

    suffix = 'hostgroup=all&style=overview&jsonoutput'
    suffix_single = 'hostgroup=%s&style=overview&jsonoutput'
    suffix_services = 'hostgroup=%s&style=detail&jsonoutput'

    def __unicode__(self):
        return self.name

    @staticmethod
    def __import_hostgroup(hostgroup, hostgroup_members, fail_logger, current_time, import_services=False):
        for i in hostgroup_members:
            try:
                h = NagiosHostStatus.objects.get(host_name=i['host_name'])
                hostgroup.hosts.add(h)
            except:
                fail_logger('Could not find host %s. Not adding it to hostgroup %s' % (i['host_name'], hostgroup.name))
        if import_services:
            NagiosServiceStatus.import_from_url(current_time, NagiosHostgroup.suffix_services % hostgroup.name)
        hostgroup.save()

    @staticmethod
    def import_single(current_time, hostgroup, import_services=False):
        """
        With this method we ca import a single hostgroup
        """
        NagiosHostgroup.run_autoclean()
        if not NagiosHostgroup.objects.filter(name=hostgroup).exists():
            raise Exception('NagiosHostgroup %s does not exist in database' % hostgroup)
        hostgroup = NagiosHostgroup.objects.get(name=hostgroup)
        hostgroup.last_database_update = current_time
        hostgroup.hosts.clear()
        items = NagiosHostgroup.get_json_from_url(NagiosHostgroup.suffix_single % hostgroup)
        nagios_list = items['status']['hostgroup_overview'][0]['members']
        log.info('Importing NagiosHostgroup %s with %s members from %s' % (hostgroup, len(nagios_list), NagiosHostgroup.get_nagios_url(NagiosHostgroup.suffix_single % hostgroup)))
        NagiosHostgroup.__import_hostgroup(hostgroup, nagios_list, log.warn, current_time, import_services)


    @staticmethod
    def import_all(current_time):
        NagiosHostgroup.run_autoclean()
        items = NagiosHostgroup.get_json_from_url(NagiosHostgroup.suffix)
        nagios_list = items['status']['hostgroup_overview']
        log.info('Importing %s NagiosHostgroup from %s' % (len(nagios_list), NagiosHostgroup.get_nagios_url(NagiosHostgroup.suffix)))
        t = timezone.now()
        for current_hostgroup in nagios_list:
            current_hostgroup_obj, created = NagiosHostgroup.objects.get_or_create(name=current_hostgroup['hostgroup_name'])
            current_hostgroup_obj.last_database_update = current_time
            current_hostgroup_obj.hosts.clear()
            NagiosHostgroup.__import_hostgroup(current_hostgroup_obj, current_hostgroup['members'], log.error, current_time)
        log.debug('Import took %s seconds' % (timezone.now() - t))


class NagiosServicegroup(NagiosImportable):
    name = models.CharField(max_length=200)
    services = models.ManyToManyField(NagiosServiceStatus)

    suffix = 'servicegroup=all&style=overview&jsonoutput'
    suffix_single = 'servicegroup=%s&style=detail&jsonoutput'

    def __unicode__(self):
        return self.name

    @staticmethod
    def __import_servicegroup(servicegroup, members, fail_logger):
        for i in members:
            try:
                s = NagiosServiceStatus.objects.get(service_description=i['service_description'],
                                                    host__host_name=i['host_name'])
                servicegroup.services.add(s)
            except:
                fail_logger('Could not find service %s on %s . Not adding it to servicegroup %s' % (i['service_description'], i['host_name'], servicegroup.name))
        servicegroup.save()

    @staticmethod
    def import_single(current_time, group_name):
        """
        With this method we can import a single servicegroup
        """
        NagiosServicegroup.run_autoclean()
        if not NagiosServicegroup.objects.filter(name=group_name).exists():
            raise Exception('NagiosServiceGroup %s does not exist in database' % group_name)
        json_result = NagiosServicegroup.get_json_from_url(NagiosServicegroup.suffix_single % group_name)
        nagios_services = json_result['status']['service_status']
        group = NagiosServicegroup.objects.get(name=group_name)
        group.last_database_update = current_time
        group.services.clear()
        log.info('Importing NagiosServicegroup %s with %s members from %s' % (group_name, len(nagios_services), NagiosServicegroup.get_nagios_url(NagiosServicegroup.suffix_single % group_name)))
        NagiosServicegroup.__import_servicegroup(group, nagios_services, log.warn)

    @staticmethod
    def import_all(current_time):
        NagiosServicegroup.run_autoclean()
        json_result = NagiosServicegroup.get_json_from_url(NagiosServicegroup.suffix)
        nagios_service_groups = json_result['status']['servicegroup_overview']
        log.info('Importing %s NagiosServicegroup from %s' % (len(nagios_service_groups), NagiosServicegroup.get_nagios_url(NagiosServicegroup.suffix)))
        t = timezone.now()
        for current_service_group in nagios_service_groups:
            current_servicegroup_obj, created = NagiosServicegroup.objects.get_or_create(name=current_service_group['servicegroup_name'])
            current_servicegroup_obj.last_database_update = current_time
            current_servicegroup_obj.services.clear()
            service_group_checks = NagiosServicegroup.get_json_from_url(NagiosServicegroup.suffix_single % current_servicegroup_obj.name)
            log.debug('Importing %s services for service group %s' % (len(service_group_checks['status']['service_status']), current_servicegroup_obj.name))
            NagiosServicegroup.__import_servicegroup(current_servicegroup_obj, service_group_checks['status']['service_status'], log.error)
        log.debug('Import took %s seconds' % (timezone.now() - t))
