from typing import Callable, Generic, Optional, TypeVar

T = TypeVar("T")
K = TypeVar("K")


class Option(Generic[T]):
    """Represents optional data.

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
        """Checks if there's no data.

        Example:
            ```python
            one = Option.some("hello, world!")
            print(one.is_none())  # False

            two = Option.none()
            print(two.is_none())  # True
            ```
        """
        return not self.__has

    def is_some(self) -> bool:
        """Checks if there's data.

        Example:
            ```python
            one = Option.some("hello, world!")
            print(one.is_some())  # True

            two = Option.none()
            print(two.is_some())  # False
            ```
        """
        return self.__has

    def _unwrap(self) -> T:
        """(unsafe)

        Unwraps this item without checking.

        Warning:
            This function does not raise a `RuntimeError` if no data is
            present. Unless it's known, do not use this function as it
            causes undefined behavior.
        """
        return self.__data  # type: ignore

    def unwrap(self) -> T:
        """Unwraps the data.

        Raises:
            RuntimeError: If no data is present (instance is `Option.none()`), this is raised.
        """
        if self.__has:
            return self.__data  # type: ignore
        else:
            raise RuntimeError("cannot call unwrap on Option 'none'")

    def unwrap_or(self, alternative: T, /) -> T:
        """Unwraps the data or use an alternative value.

        Example:
            ```python
            # Since there is data, it just unwraps
            # the original one.
            foo = Option.some("hello")
            print(foo.unwrap_or("world"))  # hello

            # Since there is NO data, it uses the
            # alternative value.
            bar = Option.none()
            print(bar.unwrap_or("world"))  # world
            ```

        Args:
            alternative: The alternative value.
        """
        if self.__has:
            return self.__data  # type: ignore
        else:
            return alternative

    def replace(self, x: T, /) -> None:
        """Replaces the current data for this instance.

        Example:
            ```python
            one = Option.some(69)
            one.replace(420)
            print(one)  # Some(420)

            two = Option.none()
            two.replace(420)
            print(two)  # Some(420)
            ```

        Returns:
            None: Nothing is returned.
        """
        self.__has = True
        self.__data = x

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
