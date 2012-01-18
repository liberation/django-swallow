from django.conf import settings


SWALLOW_CONFIGURATION_MODULES = getattr(
    settings,
    'SWALLOW_CONFIGURATION_MODULES',
    []
)

SWALLOW_DIRECTORY = settings.SWALLOW_DIRECTORY
