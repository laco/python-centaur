from importlib import import_module


class SafeImportError(Exception):
    pass


class FailedImport(object):
    def __init__(self, module_name, object_name=None, msg=None):
        self.module_name = module_name
        self.object_name = object_name
        self.msg = msg

    def __getattr__(self, name):
        raise SafeImportError(self.msg or "Missing {}".format(
            self.module_name if self.object_name is None else '.'.join([self.module_name, self.object_name])))

    def __call__(self, *args, **kwargs):
        return self.__getattr__('call')


def safe_import(module_name, *args, msg=None):
    try:
        module_ = import_module(module_name)
        if len(args) > 0:
            return _deal_with_one_element([getattr(module_, a) for a in args])
        else:
            return module_
    except ImportError:
        if len(args) > 0:
            return _deal_with_one_element([FailedImport(module_name, a, msg=msg) for a in args])
        else:
            return FailedImport(module_name, msg=msg)


def _deal_with_one_element(lst):
    if len(lst) == 1:
        return lst[0]
    else:
        return lst
