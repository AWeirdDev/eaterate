from types import EllipsisType
from typing import Union, overload, Optional

from .core import Eaterator
from .option import Option


class ERange(Eaterator[int]):
    __slots__ = ("__i", "__stop")

    __i: int
    __stop: int

    def __init__(self, start: int, stop: int):
        self.__i = start
        self.__stop = stop

    def next(self) -> Option[int]:
        if self.__i >= self.__stop:
            return Option.none()

        s = self.__i
        self.__i += 1
        return Option.some(s)

    # we can return "Eaterator[int]" because
    # inclusive() does not exist on that type,
    # type checker happi, user sad when they
    # see they cant do this again :smiling_imp:
    def inclusive(self) -> "Eaterator[int]":
        """Make this `erange` inclusive.

        Example:
        ```python
        eat = erange(0, ..., 3).inclusive()

        print(eat.next())  # Some(0)
        print(eat.next())  # Some(1)
        print(eat.next())  # Some(2)
        print(eat.next())  # Some(3)
        print(eat.next())  # Option.none()
        ```
        """
        self.__stop += 1
        return self


@overload
def erange(a: EllipsisType, b: int, c: None = None) -> ERange:
    """Creates `..b`, non-inclusive range.

    Starts from zero.

    ```python
    erange(..., 5)
    ```

    For instance, `..5` produces:
    ```python
    0
    1
    2
    3
    4
    ```

    To make it inclusive:
    ```python
    erange(..., 5).inclusive()
    ```

    Args:
        a: `...` (starts from zero).
        b: Where to end.
    """


# note: this shouldn't have inclusive()
@overload
def erange(a: int, b: EllipsisType, c: None = None) -> Eaterator[int]:
    """Creates `a..`, an infinite iterator.

    ```python
    erange(10, ...)
    ```

    For instance, `10..` produces:
    ```python
    10
    11
    12
    13
    ...  # it never ends
    ```

    Args:
        a: Where to start.
        b: `...` (infinitive).
    """


@overload
def erange(a: int, b: EllipsisType, c: int) -> ERange:
    """Creates `a..b`, non-inclusive range.

    ```python
    erange(0, ..., 3)
    ```

    For instance, `0..3` produces:
    ```python
    0
    1
    2
    ```

    To make it inclusive:
    ```python
    erange(0, ..., 3).inclusive()
    ```

    Args:
        a: Where to start.
        b: `...`
        c: Where to stop.
    """


def erange(
    a: Union[EllipsisType, int],
    b: Union[EllipsisType, int],
    c: Optional[Union[EllipsisType, int]] = None,
) -> Union[ERange, Eaterator[int]]:
    """Creates an erange (eaterate's range, lol)."""
    if isinstance(a, int):
        if isinstance(c, int):
            return ERange(a, c)
        return ERange(a, float("inf"))  # type: ignore

    else:
        return ERange(0, b)  # type: ignore
