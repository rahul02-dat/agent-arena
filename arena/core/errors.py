class ArenaError(Exception):
    pass

class EnvironmentError(ArenaError):
    pass

class AgentError(ArenaError):
    pass

class ToolError(ArenaError):
    pass

class EvaluationError(ArenaError):
    pass

class ConfigurationError(ArenaError):
    pass

class TrajectoryError(ArenaError):
    pass
