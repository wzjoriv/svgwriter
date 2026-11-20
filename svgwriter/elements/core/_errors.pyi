class UnknownAttributeError(AttributeError):
    owner: str
    attribute: str
    members: type | None

    def __init__(
        self,
        owner: str,
        name: str,
        members: type | None = None,
    ) -> None: ...
    def __str__(self) -> str: ...

class UnknownKeywordError(UnknownAttributeError, TypeError):
    def __str__(self) -> str: ...
