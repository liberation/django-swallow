class SwallowException(Exception):
    pass


class StopImport(SwallowException):
    pass


class BuilderException(SwallowException):
    pass


class StoppedImport(BuilderException):
    pass

class PopulationError(BuilderException):
    pass
