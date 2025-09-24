from collections import deque  # frozen
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    TypeVar,
    Union,
    overload,
)
import typing

from .option import Option

T = TypeVar("T")
K = TypeVar("K")

AutoIt = Union[Iterable[T], Iterator[T], "Eaterator[T]"]


def eater(it: "AutoIt[T]") -> "Eaterator[T]":
    """Creates an `Eaterator` object from either an iterable, an iterator, or an eaterator.

    - Iterable: something that can create a `Iterator` from `__iter__`.
    - Iterator: something that can be iterated with `__next__`.
    - Eaterator: iterators with additional features.

    Example:
    ```python
    r = range(100)
    eat: Eaterator = eater(r)
    ```

    Args:
        it (Iterable | Iterator | Eaterator): The iterator or iterable.
    """
    if hasattr(it, "__next__"):
        return BuiltinItEaterator(it)  # type: ignore
    elif isinstance(it, Eaterator):
        return it
    else:
        return BuiltinItEaterator(it.__iter__())


class Eaterator(Generic[T]):
    """Iterator with additional features.

    Supports `for` loops.

    Note:

    When using `len(...)` on an instance of this class, be aware that it **iterates through all items** to counts, and it cannot be re-iterated.
    This has the same effect as `.count()`.
    """

    def next(self) -> Option[T]:
        """**Required method**.

        Iterates to the next item.
        """
        raise NotImplementedError

    def map(self, fn: Callable[[T], K], /) -> "MapEaterator[T, K]":
        """Map the elements of this iterator.

        Args:
            fn: Function to transform each element.
        """
        return MapEaterator(self, fn)

    def count(self) -> int:
        """Consumes the iterator, counting the number of iterations and returning it.

        Example:
        ```python
        eat = eater(range(10)).count()
        print(eat)  # 10
        ```"""
        x = 0
        while True:
            if self.next().is_none():
                break
            x += 1
        return x

    def last(self) -> Option[T]:
        """Consumes the iterator, returning the last element.

        This method will evaluate the iterator until it returns the Option.none().
        """
        x = Option.none()
        while True:
            t = self.next()
            if t.is_none():
                break
            x = t
        return x

    def nth(self, n: int, /) -> Option[T]:
        """Returns the `n`-th element of the iterator."""
        assert n >= 0, "requires: n >= 0"

        while True:
            x = self.next()

            if n == 0:
                return x
            elif x.is_none():
                return Option.none()

            n -= 1

    def step_by(self, step: int, /) -> "StepByEaterator[T]":
        """Creates an iterator starting at the same point, but stepping by `step` at each iteration.

        This implementation ensures no number greater than `step + 1` is used.

        Example:
        ```python
        eat = eater([0, 1, 2, 3, 4, 5]).step_by(2)

        print(eat.next())  # Some(0)
        print(eat.next())  # Some(2)
        print(eat.next())  # Some(4)
        print(eat.next())  # Option.none()
        ```
        """
        if step == 1:
            return self  # type: ignore
        return StepByEaterator(self, step)

    def chain(self, eat: "AutoIt[T]", /):
        return ChainEaterator(self, eater(eat))

    def zip(self, eat: "AutoIt[K]", /) -> "ZipEaterator[T, K]":
        """'Zips up' two iterators into a single iterator of pairs.

        This returns a new iterator that will iterate over two other iterators, returning a tuple
        where the first element comes from the first iterator, and the second element comes from the second iterator.

        Stops when either one of them has stopped.

        This behaves like Python's built-in `zip()`, except only accepting one iterator only.

        Examples:

        (1) You can simply pass in two iterators.

        ```python
        eat = eater([0, 1, 2]).zip([1, 2, 3])

        print(eat.next())  # Some((0, 1))
        print(eat.next())  # Some((1, 2))
        print(eat.next())  # Some((2, 3))
        print(eat.next())  # Option.none()
        ```

        (2) Sometimes their lengths don't match. It stops whenever one of the two iterators stops.

        ```python
        eat = eater([0, 1, 2]).zip([1, 2, 3, 4, 5])

        print(eat.next())  # Some((0, 1))
        print(eat.next())  # Some((1, 2))
        print(eat.next())  # Some((2, 3))
        print(eat.next())  # Option.none()
        ```

        (3) When extracting more than two zipped iterators, beware of the `(tuple)` syntax.

        ```python
        eat = eater([0, 1, 2]).zip([2, 3, 4]).zip([4, 5, 6])

        for (a, b), c in it:
            print(a, b, c)
        ```

        Args:
            eat: The other iterator.
        """
        return ZipEaterator(self, eater(eat))

    def intersperse(self, sep: T, /) -> "IntersperseEaterator[T]":
        """Creates a new iterator which places a reference of `sep` (separator) between adjacent elements of the original iterator.

        Example:
        ```python
        eat = eater([0, 1, 2]).intersperse(10)

        print(eat.next())  # Some(0)
        print(eat.next())  # Some(10)
        print(eat.next())  # Some(1)
        print(eat.next())  # Some(10)
        print(eat.next())  # Some(2)
        print(eat.next())  # Option.none()
        ```

        Args:
            sep: The separator.
        """
        return IntersperseEaterator(self, sep)

    def for_each(self, fn: Callable[[T], Any], /) -> None:
        """Calls a function on each element of this iterator.

        To make your code Pythonic, it's recommended to just use a `for` loop.

        Example:
        ```python
        eat = eater([0, 1, 2])
        eat.for_each(lambda x: print(x))

        # Output:
        # 0
        # 1
        # 2
        ```

        Args:
            fn: The function. Takes one parameter: an element.
        """
        while True:
            x = self.next()
            if x.is_none():
                break
            fn(x._unwrap())

    def filter(self, fn: Callable[[T], bool], /) -> "FilterEaterator[T]":
        """Creates an iterator which uses a function to determine if an element should be yielded.

        Example:
        ```python
        eat = eater(range(5)).filter(lambda i: i % 2 == 0)

        print(eat.next())  # Some(0)
        print(eat.next())  # Some(2)
        print(eat.next())  # Some(4)
        print(eat.next())  # Option.none()
        ```

        Args:
            fn: The function. Takes one parameter: an element.
        """
        return FilterEaterator(self, fn)

    def enumerate(self) -> "EnumerateEaterator[T]":
        """Creates an iterator which gives the current iteration count as well as the value.

        The iterator yields pairs `(i, val)`.

        - `i`: the current index of iteration.
        - `val`: the value returned by the original iterator.

        Example:
        ```python
        eat = eater("hi!").enumerate()

        print(eat.next())  # Some((0, "h"))
        print(eat.next())  # Some((1, "i"))
        print(eat.next())  # Some((2, "!"))
        print(eat.next())  # Option.none()
        ```
        """
        return EnumerateEaterator(self)

    def peeked(self) -> "PeekedEaterator":
        """Creates an iterator that gives the current value and the next one, allowing you to peek into the next data.

        For each element, you get `(current, peeked)`, where:

        - current: the current value.
        - peeked: an `Option`, which could be `Option.none()` if no data is ahead.

        Example:
        ```python
        eat = eater("hi!").peeked()

        print(eat.next())  # Some(("h", Some("i")))
        print(eat.next())  # Some(("i", Some("!")))
        print(eat.next())  # Some(("!", Option.none()))
        print(eat.next())  # Option.none()
        ```
        """
        return PeekedEaterator(self)

    def skip(self, n: int, /) -> "SkipEaterator[T]":
        """Skip the first `n` elements.

        Args:
            n: Number of elements.
        """
        return SkipEaterator(self, n)

    def take(self, n: int, /) -> "TakeEaterator[T]":
        """Creates an iterator that only yields the first `n` elements.

        May be fewer than the requested amount.

        Args:
            n: Number of elements.
        """
        return TakeEaterator(self, n)

    @overload
    def collect(self, dst: type[list[T]], /) -> list[T]: ...

    @overload
    def collect(self, dst: type[list[T]] = list, /) -> list[T]: ...

    @overload
    def collect(self, dst: type[deque[T]], /) -> deque[T]: ...

    @overload
    def collect(self, dst: type[dict[int, T]], /) -> dict[int, T]: ...

    def collect(
        self, dst: type[Union[list[T], deque[T], dict[int, T]]] = list, /
    ) -> Union[list[T], deque[T], dict[int, T]]:
        """Collect items by iterating over all items.

        You can choose one of:
        - `list[T]`: collects to a list. **Default behavior**.
        - `deque[T]`: collects to a deque. (See `collect_deque()` for more options)
        - `dict[int, T]`: collects to a dictionary, with index keys.

        Example:
        ```python
        eat.collect(list)
        eat.collect(deque)
        eat.collect(dict)
        ```
        """
        # if no origin, possibly the user didn't use any typevar
        origin = typing.get_origin(dst) or dst

        if origin is list:
            return self.collect_list()
        elif origin is deque:
            return self.collect_deque()
        else:
            return self.collect_enumerated_dict()

    def collect_list(self) -> list[T]:
        """Collect items of this iterator to a `dict`."""
        arr = []
        while True:
            x = self.next()
            if x.is_none():
                break
            arr.append(x._unwrap())
        return arr

    def collect_deque(self, *, reverse: bool = False) -> deque[T]:
        """Collect items of this iterator to a `deque`.

        Args:
            reverse (bool, optional): Whether to reverse the order.
                Defaults to `False`.
        """
        d = deque()
        while True:
            x = self.next()
            if x.is_none():
                break
            if reverse:
                d.appendleft(x._unwrap())
            else:
                d.append(x._unwrap())
        return d

    def collect_enumerated_dict(self) -> dict[int, T]:
        """Collect items of this iterator to a `dict`, with index numbers as the key.

        In other words, you may get a dictionary like this:
        ```python
        {
            0: "h",
            1: "i",
            2: "!",
        }
        ```

        ...which is zero-indexed.

        To keep it simple, this function does not use `EnumerateEaterator` iterator.

        You can also use the `collect(dict)` instead.
        """
        d = dict()
        i = 0
        while True:
            x = self.next()
            if x.is_none():
                break
            d[i] = x._unwrap()
            i += 1
        return d

    def __iter__(self) -> Iterator[T]:
        return self

    def __len__(self) -> int:
        return self.count()

    def __next__(self) -> T:
        x = self.next()
        if x.is_some():
            return x.unwrap()
        else:
            raise StopIteration

    @overload
    def __getitem__(self, key: slice) -> "Eaterator[T]": ...

    @overload
    def __getitem__(self, key: int) -> T: ...

    def __getitem__(self, key: Union[slice, int]) -> Union[T, "Eaterator[T]"]:
        if isinstance(key, int):
            x = self.nth(key)
            if x.is_none():
                raise IndexError(f"index out of range (requested: {key})")
            else:
                return x._unwrap()
        else:
            start = key.start or 0
            stop = key.stop or 1
            step = key.step or 1

            if start < 0 or stop < 0 or step < 0:
                raise ValueError("slice(start, stop, step) cannot be negative")

            return self.skip(start).take(stop - start).step_by(step)


class BuiltinItEaterator(Eaterator[T]):
    __slots__ = ("__it",)

    __it: Iterator[T]

    def __init__(self, it: Iterator[T]):
        self.__it = it

    def next(self) -> Option[T]:
        try:
            return Option.some(self.__it.__next__())
        except StopIteration:
            return Option.none()


class MapEaterator(Generic[T, K], Eaterator[K]):
    __slots__ = ("__eat", "__f")

    __eat: Eaterator[T]
    __f: Callable[[T], K]

    def __init__(self, eat: Eaterator, f: Callable[[T], K]):
        self.__eat = eat
        self.__f = f

    def next(self) -> Option[K]:
        return self.__eat.next().map(lambda i: self.__f(i))


class StepByEaterator(Eaterator[T]):
    __slots__ = ("__eat", "__step", "__i")

    __eat: Eaterator[T]
    __step: int
    __i: int

    def __init__(self, eat: Eaterator, step: int):
        assert step >= 0, "requires: step >= 0"

        self.__eat = eat
        self.__step = step
        self.__i = 0

    def next(self) -> Option[T]:
        x = self.__eat.next()
        if self.__i == 0:
            self.__i = 1
            return x

        self.__i = (self.__i + 1) % self.__step
        return self.next()


class ChainEaterator(Eaterator[T]):
    __slots__ = ("__a", "__b", "__d")

    __a: Eaterator[T]
    __b: Eaterator[T]
    __d: bool  # done?

    def __init__(self, a: Eaterator[T], b: Eaterator[T]):
        self.__a = a
        self.__b = b
        self.__d = False

    def next(self) -> Option[T]:
        if not self.__d:
            x = self.__a.next()
            if x.is_none():
                self.__d = True
            else:
                return x

        return self.__b.next()


class ZipEaterator(Generic[T, K], Eaterator[tuple[T, K]]):
    __slots__ = ("__a", "__b")

    __a: Eaterator[T]
    __b: Eaterator[K]

    def __init__(self, a: Eaterator[T], b: Eaterator[K]):
        self.__a = a
        self.__b = b

    def next(self) -> Option[tuple[T, K]]:
        a = self.__a.next()
        b = self.__b.next()

        if a.is_some() and b.is_some():
            return Option.some((a._unwrap(), b._unwrap()))

        return Option.none()


class IntersperseEaterator(Eaterator[T]):
    __slots__ = ("__eat", "__sep", "__last", "__emits")

    __eat: Eaterator
    __sep: T
    __last: Option[T]
    __emits: bool  # whether to emit separator

    def __init__(self, eat: Eaterator, sep: T):
        self.__last = eat.next()
        self.__eat = eat
        self.__sep = sep
        self.__emits = False

    def next(self) -> Option[T]:
        if self.__last.is_none():
            return Option.none()

        if self.__emits:
            self.__emits = False
            return Option.some(self.__sep)

        self.__emits = True
        last = self.__last
        self.__last = self.__eat.next()
        return last


class FilterEaterator(Eaterator[T]):
    __slots__ = ("__eat", "__f")

    def __init__(self, eat: Eaterator[T], f: Callable[[T], bool]):
        self.__eat = eat
        self.__f = f

    def next(self) -> Option[T]:
        x = self.__eat.next()
        if x.is_none():
            return x

        if self.__f(x._unwrap()):
            return x

        return self.next()


class EnumerateEaterator(Eaterator[tuple[int, T]]):
    __eat: Eaterator[T]
    __i: int

    def __init__(self, eat: Eaterator[T]):
        self.__eat = eat
        self.__i = 0

    def next(self) -> Option[tuple[int, T]]:
        x = self.__eat.next()
        if x.is_none():
            return Option.none()

        out = Option.some((self.__i, x._unwrap()))
        self.__i += 1
        return out


class PeekedEaterator(Eaterator[tuple[T, Option[T]]]):
    __eat: Eaterator[T]
    __next: Option[T]

    def __init__(self, eat: Eaterator):
        self.__eat = eat
        self.__next = eat.next()

    def next(self) -> Option[tuple[T, Option[T]]]:
        if self.__next.is_none():
            return Option.none()

        nx = self.__next._unwrap()
        self.__next = self.__eat.next()
        return Option.some((nx, self.__next))


class SkipEaterator(Eaterator[T]):
    __eat: Eaterator[T]
    __n: int

    def __init__(self, eat: Eaterator[T], n: int):
        assert n >= 0, "requires: n >= 0"

        self.__eat = eat
        self.__n = n

    def next(self) -> Option[T]:
        x = self.__eat.next()
        if self.__n == 0:
            return x

        self.__n -= 1
        return self.next()


class TakeEaterator(Eaterator[T]):
    __slots__ = ("__eat", "__n")

    def __init__(self, eat: Eaterator[T], n: int):
        assert n >= 0, "required: n >= 0"
        self.__eat = eat
        self.__n = n

    def next(self) -> Option[T]:
        if self.__n == 0:
            return Option.none()

        self.__n -= 1
        return self.__eat.next()
