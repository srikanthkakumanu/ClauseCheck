"""Errors in the ReviewModel port contract. Adapters raise them; the api maps them to 502."""


class ModelError(Exception):
    """Base class for failures of the review model."""

    code: str = "model_error"


class ModelUnavailable(ModelError):
    """The model could not be reached: SDK error, timeout, auth failure."""

    code = "model_unavailable"


class ModelReplyInvalid(ModelError):
    """The model answered, but the reply was refused, incomplete or broke the schema."""

    code = "model_reply_invalid"
