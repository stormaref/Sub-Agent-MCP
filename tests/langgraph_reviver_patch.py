"""Apply explicit allowed_objects before langgraph creates LC_REVIVER = Reviver()."""

from langchain_core.load.load import Reviver

_original_reviver_init = Reviver.__init__


def _reviver_init_with_default_allowlist(
    self: Reviver,
    allowed_objects: object = "messages",
    *args: object,
    **kwargs: object,
) -> None:
    _original_reviver_init(self, allowed_objects, *args, **kwargs)


Reviver.__init__ = _reviver_init_with_default_allowlist  # type: ignore[method-assign]
