from typing import Optional, TypeVar, overload

from .core import Eaterator, eater

T = TypeVar("T")


class _Never: ...


NEVER = _Never()


@overload
def repeat(ele: T, /) -> Eaterator[T]:
    """Creates an `Eaterator` object that returns `ele` over and over 'til the end of time.

    There will be no counting involved.

    Example:
        ```python
        repeat("money")  # generates infinite "money"
        ```

    Args:
        ele: The element.
    """


@overload
def repeat(ele: T, n: int, /) -> Eaterator[T]:
    """Creates an `Eaterator` object that returns `ele` for `n` times.

    Example:
        ```python
        repeat("money", 10)  # generates 10 "money" (sad)
        ```

    Args:
        ele: The element.
        n (int): Number of times.
    """


def repeat(ele: T, n: Optional[int] = None, /) -> Eaterator[T]:
    if n is None:
        return eater(lambda: ele, NEVER)  # type: ignore
    else:
        return eater(range(n)).map(lambda _: ele)
