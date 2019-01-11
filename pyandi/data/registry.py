from datetime import datetime
from os.path import exists, join
import json
import warnings

from .publisher import PublisherSet
from .dataset import DatasetSet
from .activity import ActivitySet
from ..utils.exceptions import NoDataError
from ..utils.config import CONFIG


class Registry(object):
    """Class representing the IATI registry."""

    def __init__(self):
        """Construct a new Registry object.

        A warning is raised if the data is more than 7 days old.

        A ``NoDataError`` is raised if there is no data.
        """
        self._last_updated = None

        last_updated = self.last_updated
        days_ago = (datetime.now() - last_updated).days
        if days_ago > 7:
            warning_msg = 'Warning: Data was last updated {} days ' + \
                          'ago. Consider downloading a fresh ' + \
                          'data dump, using:\n\n   ' + \
                          '>>> pyandi.download.data()\n'
            warnings.warn(warning_msg.format(days_ago))

    @property
    def last_updated(self):
        """Return the datetime when the local cache was last updated.
        """
        if not self._last_updated:
            registry_path = CONFIG['paths']['registry']
            filepath = join(registry_path, 'metadata.json')
            if exists(filepath):
                with open(filepath) as handler:
                    j = json.load(handler)
                last_updated = j['updated_at']
                self._last_updated = datetime.strptime(
                    last_updated, '%Y-%m-%dT%H:%M:%SZ')
            else:
                error_msg = 'Error: No data found! ' + \
                            'Download a fresh data dump ' + \
                            'using:\n\n   ' + \
                            '>>> pyandi.download.data()\n'
                raise NoDataError(error_msg)
        return self._last_updated

    @property
    def publishers(self):
        """Return an iterator of all publishers on the registry."""
        registry_path = CONFIG['paths']['registry']
        data_path = join(registry_path, 'data', '*')
        metadata_path = join(registry_path, 'metadata', '*')
        return PublisherSet(data_path, metadata_path)

    @property
    def datasets(self):
        """Return an iterator of all IATI datasets on the registry."""
        publisher_set = self.publishers
        data_path = join(publisher_set.data_path, '*')
        metadata_path = join(publisher_set.metadata_path, '', '*')
        return DatasetSet(data_path, metadata_path)

    @property
    def activities(self):
        """Return an iterator of all IATI activities on the registry."""
        return ActivitySet(self.datasets)
