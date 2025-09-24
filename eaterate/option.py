from typing import Callable, Generic, Optional, TypeVar

T = TypeVar("T")
K = TypeVar("K")


class Option(Generic[T]):
    """Optional data.

    If no data present:

    ```python
    Option.none()
    ```

    If data is present:

    ```python
    Option.some(some_data)
    ```
    """

    __slots__ = ("__data", "__has")

    __data: Optional[T]
    __has: bool

    def __init__(self, d: Optional[T], h: bool):
        self.__data = d
        self.__has = h

    @staticmethod
    def none() -> "Option[T]":
        """Creates Option 'none' (`__NONE__`)"""
        return __NONE__

    @staticmethod
    def some(d: T) -> "Option[T]":
        """Creates Option 'some'

        Args:
            d: The data.
        """
        return Option(d, True)

    def is_none(self) -> bool:
        """Checks if there's no data."""
        return not self.__has

    def is_some(self) -> bool:
        """Checks if there's data."""
        return self.__has

    def _unwrap(self) -> T:
        """(unsafe)

        Unwraps this item without checking.
        """
        return self.__data  # type: ignore

    def unwrap(self) -> T:
        if self.__has:
            return self.__data  # type: ignore
        else:
            raise RuntimeError("cannot call unwrap on Option 'none'")

    def unwrap_or(self, alternative: T, /) -> T:
        if self.__has:
            return self.__data  # type: ignore
        else:
            return alternative

    def replace(self, x: T, /) -> "Option[T]":
        self.__has = True
        self.__data = x
        return self

    def map(self, fn: Callable[[T], K], /) -> "Option[K]":
        if self.is_some():
            return Option.some(fn(self.__data))  # type: ignore
        else:
            return self  # type: ignore

    def __hash__(self) -> int:
        return 0

    def __bool__(self) -> bool:
        return False

    def __str__(self) -> str:
        if self.__has:
            return f"Some({self.__data!r})"
        else:
            return "Option.none()"

    def __repr__(self) -> str:
        return self.__str__()


__NONE__ = Option(None, False)
