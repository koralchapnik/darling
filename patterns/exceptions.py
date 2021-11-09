class InvalidConditionParams(Exception):
    def __init__(self, message, errors=None):
        custom_msg = f'There was an error with the condition parameters.' \
                     f'The parameters are: {message}'
        super().__init__(custom_msg)


class EventTypeNotInTree(Exception):
    pass


class NonMatchParents(Exception):
    pass


class NoMoreEvents(Exception):
    pass
