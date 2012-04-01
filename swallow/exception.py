class SwallowException(Exception):
    pass


class StopImport(SwallowException):
    """Stop current builder import"""
    pass


class StopMapper(SwallowException):
    """Raise this exception to stop the current mapper processing"""
    pass


class StopBuilder(SwallowException):
    """Raise this exception to stop the current builder processing"""
    pass


class StopConfig(SwallowException):
    """Raise this exception to stop the full config run"""
    pass


class PostponeBuilder(SwallowException):
    """Raise this exception to stop process an endpoint file and keep it to next run."""
    pass


class BuilderException(SwallowException):
    pass


class StoppedImport(BuilderException):
    pass


class PopulationError(BuilderException):
    pass
