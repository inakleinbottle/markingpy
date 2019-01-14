import tempfile
from pathlib import Path
from enum import Enum
from secrets import token_urlsafe


class EnvironmentStatus(Enum):
    created = 0
    modified = 1


class File:

    def __init__(self, name, readable=True, writable=True,
                 executable=True, exists=True, parent=None,
                 content=None):
        self.name = name
        self.readable = readable
        self.writable = writable
        self.executable = executable
        self.exists = exists
        self.parents = parent
        self.content = content
        self.status = None

    def init(self):
        if not self.parent.status == EnvironmentStatus.created:
            raise RuntimeError('Cannot init ')
        if self.status is not None:
            raise RuntimeError('File already instantiated')

        path = self.parent.get_path() / self.name
        if self.content:
            path.write_text(self.content)
        else:
            path.touch()
        self.status = EnvironmentStatus.created


class Environment:

    def __init__(self, *, name=None, environ_vars=None, parent=None):
        self.name = name or token_urlsafe(16)
        self.environ_vars = environ_vars
        self.sub_environments = {}
        self.parent = parent
        self.files = []
        self.status = None
        self._path = None  # Do not modify
        self._temp_dir = None

    def init(self):
        if self.parent is not None:
            if self.parent.status is not None:
                raise RuntimeError('Parent not yet created')
            path = self.get_path()
            path.mkdir()
        else:
            dir_ = self._temp_dir = tempfile.TemporaryDirectory()
            self._path = Path(dir_.name)
        self.status = EnvironmentStatus.created
        for file in self.files:
            file.init()
        for sub_env in self.sub_environments:
            sub_env.init()

    def cleanup(self):
        if self.parent is not None:
            return self.get_parent().cleanup()
        self._temp_dir.cleanup()

    def add_sub_environment(self, name):
        if name in self.sub_environments:
            env = self.sub_environments[name]
        else:
            env = Environment(name=name, parent=self)
            self.sub_environments[name] = env
        return env

    def create_parents(self, parents):
        if parents is None:
            parent = self
        elif isinstance(parents, str):
            components = parents.split('/')  # Unix style paths
            curr = self
            for comp in components:
                curr = curr.add_sub_environment(comp)
            parent = curr
        elif isinstance(parents, (list, tuple)):
            curr = self
            for comp in parents:
                curr = curr.add_sub_environment(comp)
            parent = curr
        else:
            raise RuntimeError('Could not create sub environment')
        return parent

    def get_parent(self):
        if self.parent is None:
            return self
        else:
            return self.parent.get_parent()

    def get_path(self):
        if not self.status == EnvironmentStatus.created:
            raise RuntimeError('Environment not created')
        if self.parent is not None:
            path = self.parent.get_path() / self.name
        else:
            path = self._path
        return path

    def file(self, name=None, readable=True, writeable=True, executable=False,
             exists=True, parents=None, extension='.py', params=None):
        if isinstance(name, str):
            name_, name = name, None
        else:
            name_ = None
        params = dict(params) if params is not None else {}
        parent = self.create_parents(parents)

        def decorator(func):
            nonlocal name_
            name_ = name_ if name_ else func.__name__ + extension
            content = func(**params)
            file = File(name_, readable, writeable, executable, exists, parent,
                        content)
            return file

        if name is None:
            return decorator
        else:
            return decorator(name)


