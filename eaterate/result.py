from typing import Generic, Optional, TypeVar

T = TypeVar("T")
E = TypeVar("E", bound=Exception)


class Result(Generic[T, E]):
    """Either a value of error."""

    __slots__ = ("__data", "__err")

    __data: Optional[T]
    __err: Optional[E]

    def __init__(self, data: Optional[T], err: Optional[E]):
        self.__data = data
        self.__err = err

    @staticmethod
    def err(e: E) -> "Result[T, E]":
        return Result(None, e)

    @staticmethod
    def ok(d: T) -> "Result[T, E]":
        return Result(d, None)

    def is_err(self) -> bool:
        return self.err is not None

    def is_ok(self) -> bool:
        return self.err is None

    def unwrap(self) -> T:
        if self.is_err():
            raise RuntimeError("cannot call unwrap on Result 'err'")
        return self.__data  # type: ignore

    def _unwrap(self) -> T:
        """(unsafe)

        Unwraps the value without checking.
        """
        return self.__data  # type: ignore

    def unwrap_err(self) -> E:
        if self.is_ok():
            raise RuntimeError("cannot call unwrap_err on Result 'ok'")
        return self.__err  # type: ignore

    def _unwrap_err(self) -> E:
        """(unsafe)

        Unwraps the error without checking.
        """
        return self.__err  # type: ignore
