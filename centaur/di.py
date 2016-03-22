

def _depends_on_cls_factory(dependencies, BaseCls):
    def init(self, *args, **kwargs):
        _dependencies_dict = {}
        try:
            for d in dependencies:
                _dependencies_dict[d] = kwargs.pop(d)
        except KeyError as e:
            raise TypeError("Missing dependency {}".format(str(e)))
        super(BaseCls, self).__init__(*args, **kwargs)
        for d, v in _dependencies_dict.items():
            setattr(self, d, v)

    cls_name_partial = ''.join([d.title() for d in dependencies])

    mixin_cls = type(
        'DependsOn' + cls_name_partial + 'Mixin',
        (object, ),
        {})
    mixin_cls.__init__ = init

    new_cls = type(
        BaseCls.__name__ + 'WithDependencies' + cls_name_partial,
        (mixin_cls, BaseCls),
        {})
    return new_cls


def depends_on(*dependencies):
    def cls_decorator(cls):
        return _depends_on_cls_factory(dependencies, cls)
    return cls_decorator
