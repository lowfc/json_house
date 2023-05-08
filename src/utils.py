import os
from hashlib import md5
from pathlib import Path
from typing import Optional
from random import randbytes
from datetime import datetime
from json import loads, JSONDecodeError

import yaml
from lxml import etree


class MetaSingleton(type):
    """ Base realisation of singleton """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(MetaSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class GetRoot(metaclass=MetaSingleton):
    """ Singleton to get project path """

    __root: Path = None

    def get_root(self):
        if self.__root is None:
            self.__root = Path(__file__).parent.parent
        return self.__root


class Config(metaclass=MetaSingleton):
    """ Singleton to read config """

    __configs = {}

    def __read_config(self, conf_name) -> bool:
        path = GetRoot().get_root()
        file_path = path / "config.d" / (conf_name + ".yml")
        if os.path.isfile(file_path):
            with open(file_path, "r") as file:
                self.__configs[conf_name] = yaml.load(file.read(), yaml.Loader)
                return True
        return False

    def get(self, conf_name, parameter) -> Optional[any]:
        success = True
        if conf_name not in self.__configs.keys():
            success = self.__read_config(conf_name)
        if success:
            return self.__configs[conf_name].get(parameter)
        return None


def get_hash(salt: str) -> str:
    all_salt = str(datetime.now().timestamp()).encode() + randbytes(256) + salt.encode()
    md = md5(all_salt)
    return md.hexdigest()


def validate_content(content_type: str, data: any) -> bool:
    match content_type:
        case "json":
            try:
                loads(data)
            except JSONDecodeError:
                return False
        case "xml":
            try:
                etree.XML(data)
            except etree.XMLSyntaxError:
                return False
    return True
