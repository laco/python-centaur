
def _construct_exception_from_result(result):
    option_msgs = {
        'regex': 'Bad format'
    }
    print(result)
    if result.option_name in option_msgs:
        return option_msgs[result.option_name]


class _Result(object):
    def __init__(self, result, value, option_name, option_value):
        self.result = result
        self.value = value
        self.option_name = option_name
        self.option_value = option_value

    def __bool__(self):
        if isinstance(self.result, list):
            return bool(all(self.result))
        else:
            return bool(self.result)

    @property
    def failed(self):
        return not bool(self)

    def __repr__(self):
        if isinstance(self.result, list):
            return ", ".join([repr(r) for r in self.result])
        else:
            return "_Result{}({}| {}: {})".format(self.result, repr(self.value), self.option_name, self.option_value)
