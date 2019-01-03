import webbrowser
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from ..standard.schema import get_schema
from ..utils.abstract import GenericSet
from ..utils.exceptions import SchemaError
from ..utils.querybuilder import XPathQueryBuilder

from lxml import etree as ET


class ActivitySet(GenericSet):
    """Class representing a grouping of ``Activity`` objects.

    Objects in this grouping can be filtered and iterated over.
    Queries are only constructed and run when needed, so they
    can be efficient.
    """

    def __init__(self, datasets, **kwargs):
        super(ActivitySet, self).__init__()
        self._key = 'iati_identifier'
        self._filters = [
            'id', 'iati_identifier', 'title', 'description',
            'location', 'sector', 'planned_start',
            'actual_start', 'planned_end', 'actual_end',
            'xpath',
        ]
        self._wheres = kwargs
        self._instance_class = Activity

        self.datasets = datasets
        self._filetype = 'activity'
        self._element = 'iati-activity'

    def __len__(self):
        total = 0
        for dataset in self.datasets:
            if dataset.filetype != self._filetype:
                continue
            if not dataset.is_valid():
                continue
            try:
                schema = get_schema(dataset.filetype, dataset.version)
            except SchemaError:
                continue
            prefix = '//' + self._element
            query = XPathQueryBuilder(
                schema,
                prefix=prefix,
                count=True
            ).where(**self._wheres)
            total += int(dataset.etree.xpath(query))
        return total

    def _query(self, schema):
        prefix = '//' + self._element
        return XPathQueryBuilder(
            schema,
            prefix=prefix,
        ).where(**self._wheres)

    def __iter__(self):
        for dataset in self.datasets:
            if dataset.filetype != self._filetype:
                continue
            if not dataset.is_valid():
                continue
            try:
                schema = get_schema(dataset.filetype, dataset.version)
            except SchemaError:
                continue
            activity_etrees = dataset.etree.xpath(self._query(schema))
            for tree in activity_etrees:
                yield self._instance_class(tree, dataset, schema)


class Activity(object):
    """Class representing an IATI activity."""

    def __init__(self, etree, dataset=None, schema=None):
        self.etree = etree
        self.dataset = dataset
        self._schema = schema
        self.version = self.schema.version

    def __repr__(self):
        id_ = self.iati_identifier
        id_ = id_ if id_ else '[No identifier]'
        return '<{} ({})>'.format(self.__class__.__name__, id_)

    def show(self):
        """Open a new browser tab to the d-portal.org page
        for this dataset.
        """
        params = {'aid': self.iati_identifier}
        url = 'http://d-portal.org/q.html?{}'.format(urlencode(params))
        webbrowser.open_new_tab(url)

    @property
    def schema(self):
        if not self._schema:
            # TODO: Add a schema guesser,
            # based on the activity XML
            pass
        return self._schema

    @property
    def xml(self):
        """Return the raw XML of this activity, as a byte-string."""
        return bytes(ET.tostring(self.etree))

    @property
    def iati_identifier(self):
        """Return the iati-identifier for this activity,
        or ``None`` if it isn't provided.
        """
        id_ = self.schema.iati_identifier().run(self.etree)
        if len(id_) > 0:
            return id_[0].strip()
        return None

    @property
    def id(self):
        """Alias of ``iati_identifier``."""
        return self.iati_identifier

    @property
    def title(self):
        """Return a list of titles for this activity."""
        return self.schema.title().run(self.etree)

    @property
    def description(self):
        """Return a list of descriptions for this activity."""
        return self.schema.description().run(self.etree)

    @property
    def location(self):
        """Return a list of locations for this activity."""
        return self.schema.location().run(self.etree)

    @property
    def sector(self):
        """Return a list of sectors for this activity."""
        return self.schema.sector().run(self.etree)

    @property
    def planned_start(self):
        """Return the planned start date for this activity,
        as a python ``date``.
        """
        date = self.schema.planned_start().run(self.etree)
        return date[0] if len(date) > 0 else None

    @property
    def actual_start(self):
        """Return the actual start date for this activity,
        as a python ``date``.
        """
        date = self.schema.actual_start().run(self.etree)
        return date[0] if len(date) > 0 else None

    @property
    def start(self):
        """Return the actual start date for this activity,
        if present. Otherwise, return the planned start.
        """
        start = self.actual_start
        if start:
            return start
        return self.planned_start

    @property
    def planned_end(self):
        """Return the planned end date for this activity,
        as a python ``date``.
        """
        date = self.schema.planned_end().run(self.etree)
        return date[0] if len(date) > 0 else None

    @property
    def actual_end(self):
        """Return the actual end date for this activity,
        as a python ``date``.
        """
        date = self.schema.actual_end().run(self.etree)
        return date[0] if len(date) > 0 else None

    @property
    def end(self):
        """Return the actual end date for this activity,
        if present. Otherwise, return the planned end.
        """
        end = self.actual_end
        if end:
            return end
        return self.planned_end
