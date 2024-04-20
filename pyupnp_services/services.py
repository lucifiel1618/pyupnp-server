import functools
import logging
from pathlib import Path
import re
import dataclasses
from urllib.parse import ParseResult, urlparse, quote
from typing import Any, Callable, ClassVar, Literal, Optional, Self
import uuid

from django.conf import settings
from django.db.models import ForeignKey
import filebrowser.sites
import filebrowser.base

from .models import Device, Service

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')
logger.info('services?')


def _get_model_fields(model, *, excluded=set()) -> dict[str, Any]:
    fields = (
        f.name for f in model._meta.fields
        if not isinstance(f, ForeignKey) and f.name not in excluded and f.name != 'id'
    )
    # print(f'{fields=}')
    return {f: getattr(model, f) for f in fields}


def initialize_device(device: Device, url: str, path: str) -> None:
    parsed_location = ParseResult('http', url, path, '', '', '')
    device.UDN = f'uuid:{uuid.uuid5(uuid.uuid5(uuid.NAMESPACE_DNS, device.modelDescription), parsed_location.geturl())}'
    device.presentationURL = parsed_location._replace(path='').geturl()
    content_directory = Service.create('ContentDirectory', 1, device=device)

    browse = content_directory.action_set.create(name='Browse')

    browse.argument_set.create(name='ObjectID', direction='in', relatedStateVariable='A_ARG_TYPE_ObjectID')
    browse.argument_set.create(name='BrowseFlag', direction='in', relatedStateVariable='A_ARG_TYPE_BrowseFlag')
    browse.argument_set.create(name='StartingIndex', direction='in', relatedStateVariable='A_ARG_TYPE_Index')
    browse.argument_set.create(name='RequestedCount', direction='in', relatedStateVariable='A_ARG_TYPE_Count')
    browse.argument_set.create(name='Filter', direction='in', relatedStateVariable='A_ARG_TYPE_Filter')
    browse.argument_set.create(name='SortCriteria', direction='in', relatedStateVariable='A_ARG_TYPE_SortCriteria')
    browse.argument_set.create(name='Result', direction='out', relatedStateVariable='A_ARG_TYPE_Result')
    browse.argument_set.create(name='NumberReturned', direction='out', relatedStateVariable='A_ARG_TYPE_Count')
    browse.argument_set.create(name='TotalMatches', direction='out', relatedStateVariable='A_ARG_TYPE_Count')

    content_directory.statevariable_set.create(name='A_ARG_TYPE_ObjectID', dataType='string')
    content_directory.statevariable_set.create(name='A_ARG_TYPE_Result', dataType='string')
    content_directory.statevariable_set.create(name='A_ARG_TYPE_Index', dataType='ui4')
    content_directory.statevariable_set.create(name='A_ARG_TYPE_Count', dataType='ui4')
    content_directory.statevariable_set.create(name='A_ARG_TYPE_Filter', dataType='string')
    content_directory.statevariable_set.create(name='A_ARG_TYPE_SortCriteria', dataType='string')
    browse_flag = content_directory.statevariable_set.create(name='A_ARG_TYPE_BrowseFlag', dataType='string')

    browse_flag.allowedvalue_set.create(allowedValue='BrowseMetadata')
    browse_flag.allowedvalue_set.create(allowedValue='BrowseDirectChildren')

    Service.create('ConnectionManager', 1, device=device)

    device.save()


def get_device_detail(device):
    return _get_model_fields(device, excluded={'deviceId'})


def get_all_service_details(device):
    return [_get_model_fields(service) for service in device.service_set.all()]


def get_all_action_arugmentlist_pairs(service):
    return [(_get_model_fields(action), get_argumentlist(action)) for action in service.action_set.all()]


def get_argumentlist(action):
    return [_get_model_fields(argument) for argument in action.argument_set.all()]


def get_all_statevar_allowedvaluelist_pairs(service):
    return [
        (statevar.sendEvents, _get_model_fields(statevar, excluded={'sendEvents'}), get_allowedvaluelist(statevar))
        for statevar in service.statevariable_set.all()
    ]


def get_allowedvaluelist(statevar):
    return [
        _get_model_fields(allowedvalue)
        for allowedvalue in statevar.allowedvalue_set.all()
    ]


@dataclasses.dataclass(frozen=True, slots=True)
class Entry:
    id: str
    title: str
    type: tuple[Literal['container', 'item'], str]
    path: Path
    parent: Optional[str] = None
    url: Optional[str] = None
    mimetype: Optional[str] = None
    ROOT_PATH: ClassVar[Path] = Path(filebrowser.sites.site.storage.location, filebrowser.sites.site.directory)
    OBJECT_ID_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"(?P<device>\d+)(?P<view>(?:\$\d+){0,1})(?P<levels>(?:\$\d+)*)(?P<resource>R{0,1})"
    )
    BASE_URL: ClassVar[Optional[str]] = None

    @staticmethod
    def _get_object_id_parts(p: Path, root: Path) -> tuple[str, str]:
        if p == root:
            # '0' is equivalent to device root, and '0$0' to 'By Folder'.
            return '0$0', ''
        return ''.join(Entry._get_object_id_parts(p.parent, root)), f'${p.stat().st_ino}'

    @classmethod
    def get_object_id_parts(cls, p: Path) -> tuple[str, str]:
        return cls._get_object_id_parts(p, cls.ROOT_PATH)

    @classmethod
    def from_fileobject(cls, fileobject: filebrowser.base.FileObject) -> Self:
        parent, base = cls.get_object_id_parts(Path(fileobject.path_full))
        title = fileobject.filename_root
        type0 = 'container' if fileobject.is_folder else 'item'
        id = f'{parent}{base}{"R" if type0 == "item" else ""}'
        if fileobject.is_folder:
            url = None
            mimetype = None
            type1 = '.storageFolder'
        else:
            url = cls.get_fileobject_url(fileobject)
            mimetype = fileobject.mimetype[0]
            type1 = f'.{mimetype.split("/", 1)[0]}Item' if mimetype is not None else ''
        return cls(id, title, (type0, type1), fileobject.path_full, parent, url, mimetype)

    def to_fileobject(self) -> filebrowser.base.FileObject:
        return filebrowser.base.FileObject(self.path)

    def as_resource(self) -> Self:
        if self.type[0] == 'container':
            mimetype = 'video/mp2t'
            return type(self)(
                f'{self.id}R',
                self.title,
                ('item', f'.{mimetype.split("/", 1)[0]}Item'),
                self.path,
                self.parent,
                self.get_fileobject_url(self.to_fileobject()),
                mimetype
            )
        return self

    @classmethod
    def get_fileobject_url(cls, fileobject: filebrowser.base.FileObject) -> str:
        parsed_location = urlparse(settings.DATABASE_URL)
        hostname = parsed_location.hostname
        if cls.BASE_URL is not None and hostname == '0.0.0.0':
            parsed_location = parsed_location._replace(
                netloc=f'{cls.BASE_URL}{parsed_location.netloc[len(hostname):]}'
            )
        path = str(Path(parsed_location.path, quote(str(Path(fileobject.path).relative_to(cls.ROOT_PATH)))))
        url = parsed_location._replace(path=path).geturl()
        logger.info(f'{url=}')
        return url

    @classmethod
    @functools.lru_cache(maxsize=100)
    def get_path_from_object_id(cls, trimmed_object_id: str) -> Path:
        parent, base = trimmed_object_id.rsplit('$', 1)
        base_id = int(base)
        directory = cls.get_path_from_object_id(parent) if parent != '' else cls.ROOT_PATH
        for f in directory.iterdir():
            if f.stat().st_ino == base_id:
                return f
        raise FileNotFoundError(f'File corresponding to ObjectID `{trimmed_object_id}` is not found.')

    @classmethod
    def from_object_id(cls, object_id: str) -> Self:
        m = cls.OBJECT_ID_PATTERN.match(object_id)
        if m is None:
            return cls.from_object_id('0')
        d = m.groupdict()
        if not (view := d['view']):
            return cls(object_id, '', ('container', ''), cls.ROOT_PATH, parent=m['device'])
        if not (levels := d['levels']):
            if view == '$0':
                title = 'By Folder'
            else:
                raise NotImplementedError(
                    f'ObjectID with unknown view option: `{view}`. Possibly not yet implemented.'
                )
            return cls(object_id, title, ('container', ''), cls.ROOT_PATH, parent=m['device'])
        fileobject = filebrowser.base.FileObject(cls.get_path_from_object_id(levels))
        obj = cls.from_fileobject(fileobject)
        if d['resource'] == 'R':
            obj = obj.as_resource()
        return obj


def control_browse(
    ObjectID: str,
    StartingIndex: int,
    RequestedCount: int,
    BrowseFlag: str,
    Filter: str = '',
    SortCriteria: str = '',
    *,
    dir_as_item: bool = True,
    filter_func: Callable[[filebrowser.base.FileObject], bool] = (
        lambda fileobject: fileobject.filetype in {'Video', 'Image', 'Music', 'Folder'}
    ),
    base_url: Optional[str] = None,
    **kwds
):
    for arg_name, arg_v in kwds:
        logger.warn(f'Browse Control recieves unknown arugment: `{arg_name} = {arg_v}`')
    entries: list[Entry] = []

    parsed = urlparse(f'//{base_url}')
    if parsed.port is not None:
        parsed = parsed._replace(netloc=parsed.netloc[:-(1 + len(str(parsed.port)))])
    Entry.BASE_URL = parsed.netloc

    if BrowseFlag == 'BrowseDirectChildren':
        parent_en = Entry.from_object_id(ObjectID)
        if '$' not in parent_en.id:
            entries = [Entry.from_object_id(f'{parent_en.id}$0')]
            n = 1
        elif parent_en.type[0] == 'item':
            entries = [parent_en]
            n = 1
        else:
            parent_path = parent_en.path
            filelisting = filebrowser.base.FileListing(
                parent_path,
                sorting_by=None,
                sorting_order=None,
                filter_func=filter_func
            )
            all_files: list[filebrowser.base.FileObject] = filelisting.files_listing_filtered()
            n = 0
            stop = (StartingIndex + RequestedCount) if RequestedCount > 0 else None
            no_stop = stop is None
            for f in all_files:
                if (StartingIndex <= n) and (no_stop or n < stop):
                    en = Entry.from_fileobject(f)
                    entries.append(en)
                n += 1
                if dir_as_item and f.is_folder:
                    if (StartingIndex <= n) and (no_stop or n < stop):
                        en = en.as_resource()
                        entries.append(en)
                    n += 1
        number_returned = len(entries)
        total_matches = n
        return {
            'result_entries': entries,
            'text_entries': {'NumberReturned': number_returned, 'TotalMatches': total_matches}
        }
    raise NotImplementedError(f'Unknown BrowseFlag: `{BrowseFlag}`. Possibly not yet implemented.')
