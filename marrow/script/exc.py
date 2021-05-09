class ExitException(Exception):
	pass


class ScriptError(Exception):
	pass


class MalformedArguments(ScriptError):
	pass


class InspectionComplete(Exception):
	pass


class InspectionFailed(Exception):
	pass