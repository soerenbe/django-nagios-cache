# django-nagios-cache

## Overview
This Django package provide Models for syncing data fom a Icinga/Nagios instance.
This may useful if you want to make queries to you monitoring system without
directly connect to it for each lookup.

It is currently tested with Icinga 1.10.3.


The package consist of 2 main parts

### Django Models
This is the datastruructure. I directly correlates with the Nagios/Icinga Services,
Servicegroups, Hosts and Hostgroups.

### Management Command
The package provides a Management Command to sync the Data from the Nagios/Icinga Server.
You may also sync only parts of monitoring data e.g. only specific Hostgroups or Servicegroups
## Installation
To install simply fetch it from pypi.
```python
pip install django-nagios-cache
```
After that you have to add ```nagios_cache``` to your ```INSTALLED_APPS``` and
run
```
python manage.py migrate nagios_cache
```
This will add the 4 Models to your database.

## Configuration
django-nagios-cache reads 4 configuration variables from your settings.py:
```python
NAGIOS_CACHE_URL = "https://monitoring.example.org/cgi-bin/icinga/status.cgi"
NAGIOS_CACHE_USER' = "nagios_user",
NAGIOS_CACHE_PASSWORD' = "password_4_nagios_123",
NAGIOS_CACHE_AUTOCLEAN = False
NAGIOS_CACHE_AUTOCLEAN_DAYS = 5
```
You MUST specify ```NAGIOS_CACHE_URLNAGIOS_CACHE_URL```, while the other 2 are optional.
If there are no authentication details, ```django-nagios-cache``` will fetch the
data without authentication.
If you set ```NAGIOS_CACHE_AUTOCLEAN = True``` every query will automatically
clean up the last ```NAGIOS_CACHE_AUTOCLEAN_DAYS``` unsynced entries.

## Usage
At the first run you may want to execute
```
python manage.py nagios_sync
```

This will sync everything. Note this could take some time. On my machine 20000 checks, 1500 hosts, 200 hostgroups and 10 servicegroups this take about 4 minutes.

Later you may chose only to sync specific parts. Have a look at
```
./manage.py nagios_sync --help
...
  --hostgroups [HOSTGROUPS [HOSTGROUPS ...]]
                        Only sync the given hostgroups
  --servicegroups [SERVICEGROUPS [SERVICEGROUPS ...]]
                        Only sync the given servicegroups
  --sync-hosts          Sync hosts
  --sync-services       Sync services
  --sync-hostgroups     Sync hostgroups
  --sync-servicegroups  Sync servicegroups
  --clean               Cleanup database entries that are old than 1 day
```
You can add this script to a crontab or use the API for a celery task. Have a
look at ```nagios_cache/management/commands/nagios_sync```. There are the calls for
the commandline options above.
```python
from django.utils import timezone

t = timezone.now()

NagiosHostStatus.clean_old(t)
NagiosServiceStatus.import_all(t)
NagiosHostgroup.import_all(t)
NagiosServicegroup.import_single(t, 'dns')
```
