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
E = TypeVar("E", bound=Exception)

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
    elif hasattr(it, "__iter__"):
        return BuiltinItEaterator(it.__iter__())
    else:
        raise TypeError(
            f"expected either an iterable, an iterator, or an Eaterator object, got: {type(it)!r}"
        )


class Eaterator(Generic[T]):
    """Iterator with additional features.

    Supports `for` loops.

    Example:
    ```python
    eat = eater([1, 2, 3]).chain([4, 5, 6])
    eat.collect(list)  # [1, 2, 3, 4, 5, 6]
    ```
    """

    def next(self) -> Option[T]:
        """**Required method**.

        Iterates to the next item.

        Example:
        ```python
        class MyEaterator(Eaterator[int]):
            def next(self) -> Option[int]:
                if exhausted:
                    # the iterator stops when Option.none() is present
                    return Option.none()
                else:
                    # this is the actual value you'd like to yield
                    return Option.some(1)

        ```
        """
        raise NotImplementedError

    def map(self, fn: Callable[[T], K], /) -> "MapEaterator[T, K]":
        """Map the elements of this iterator.

        Args:
            fn: Function to transform each element.
        """
        return MapEaterator(self, fn)

    def all(self, fn: Callable[[T], bool], /) -> bool:
        """Tests if every element of the iterator matches a predicate.

        Equivalents to Python's `all()`.
        """
        while True:
            x = self.next().map(fn)
            if x.is_none():
                return True

            if not x._unwrap():
                return False

    def any(self, fn: Callable[[T], bool], /) -> bool:
        """Tests if an element of the iterator matches a predicate.

        Equivalents to Python's `any()`.
        """
        while True:
            x = self.next().map(fn)
            if x.is_none():
                return False

            if x._unwrap():
                return True

    def find(self, fn: Callable[[T], bool], /) -> Option[T]:
        """Searches for an element of the iterator that satisfies a predicate.

        Example:
        ```python
        eat = eater([1, 2, 3]).find(lambda x: x % 2 == 0)
        print(eat)  # Some(2)
        ```

        Returns:
            Option[T]: An `Option` object, which is **NOT** `typing.Optional[T]`.
        """
        while True:
            x = self.next()
            if x.is_none():
                return Option.none()

            if fn(x._unwrap()):
                return x

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

    def chain(self, *eats: "AutoIt[T]") -> "ChainEaterator[T]":
        """Chain multiple iterators into one.

        Args:
            *eats (`AutoIt[T]`): Other iterators.
        """
        e = ChainEaterator(self, eater(eats[0]))
        for itm in eats[1:]:
            e = ChainEaterator(e, eater(itm))
        return e

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

    def try_for_each(
        self, fn: Callable[[T], Any], _errhint: type[E] = Exception, /
    ) -> Union[E, None]:  # not to be confused with Option
        """Calls a falliable function on each element of this iterator.

        Stops when one iteration has an error (exception) occurred.

        Example:
        Let's assume you have a function defined for `try_for_each` that may fail, as well as
        an iterator. You'll notice that `try_for_each` gracefully catches the error, and returns it.
        ```python
        def nah(x: int):
            raise RuntimeError("hell nawh!")

        # the iterator
        eat = eater([1, 2, 3])

        err = eat.try_for_each(nah)
        if err is not None:
            print(err)  # hell nawh!
        else:
            print('ok')
        ```

        If needed, you can also provide the type checker with exception hints.
        If provided, only that exception will be caught.

        ```python
        eat.try_for_each(nah, RuntimeError)
        ```

        Args:
            fn (Callable): The function. Takes one parameter: an element.
            _errhint (Exception, optional): Type hint that specifies what error may occur or be caught.
        """
        while True:
            x = self.next()
            if x.is_none():
                break
            try:
                fn(x._unwrap())
            except _errhint as err:
                return err

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

    @overload
    def collect(self, dst: type[str], /) -> str: ...

    @overload
    def collect(self, dst: type[set], /) -> set[T]: ...

    def collect(
        self, dst: type[Union[list[T], deque[T], dict[int, T], str, set]] = list, /
    ) -> Union[list[T], deque[T], dict[int, T], str, set]:
        """Collect items by iterating over all items. Defaults to `list`.

        You can choose one of:
        - `list[T]`: collects to a list. **Default behavior**.
        - `deque[T]`: collects to a deque. (See `collect_deque()` for more options)
        - `dict[int, T]`: collects to a dictionary, with index keys.
        - `str`: collects to a string.
        - `set`: collects to a set.

        Example:
        ```python
        eat.collect(list)
        eat.collect(deque)
        eat.collect(dict)
        eat.collect(str)
        eat.collect(set)
        ```

        You can add additional annotations, if needed:
        ```python
        # eaterate won't read 'int', it only recognizes 'list'
        # you need to ensure the type yourself, both in type
        # checking and runtime
        eat.collect(list[int])
        ```
        """
        # if no origin, possibly the user didn't use any typevar
        origin = typing.get_origin(dst) or dst

        if origin is list:
            return self.collect_list()
        elif origin is deque:
            return self.collect_deque()
        elif origin is str:
            return self.collect_str()
        elif origin is dict:
            return self.collect_enumerated_dict()
        elif origin is set:
            return self.collect_set()
        else:
            raise NotImplementedError(f"unknown collector: {origin!r} (from: {dst!r})")

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

    def collect_str(self) -> str:
        """Collect items of this iterator to a `str`.

        Example:
        ```python
        eat = eater(["m", "o", "n", "e", "y"])
        eat.collect_str()  # money
        ```
        """
        s = ""
        while True:
            x = self.next()
            if x.is_none():
                break
            s += str(x._unwrap())
        return s

    def collect_set(self) -> "set[T]":
        """Collects items of this iterator to a `set`, which ensures there are no repeated items.

        Example:
        ```python
        res = eater([0, 0, 1, 2]).collect_set()
        print(res)  # {0, 1, 2}
        ```
        """
        return set(self)

    def flatten(self) -> "FlattenEaterator[T]":
        """Creates an iterator that flattens nested structure.

        This is useful when you have *an iterator of iterators* or *an iterator of elements* that can be turned into iterators,
        and you'd like to flatten them to one layer only.

        **Important**: **requires each element to satisfy `Iterable[K] | Iterator[K] | Eaterator[K]`** (`AutoIt`).

        Example:
        ```python
        eat = (
            eater([
                ["hello", "world"],
                ["multi", "layer"]
            ])
            .flatten()
        )

        eat.next()  # Some("hello")
        eat.next()  # Some("world")
        eat.next()  # Some("multi")
        eat.next()  # Some("layer")
        eat.next()  # Option.none()
        ```
        """
        return FlattenEaterator(self)  # type: ignore

    def fold(self, init: K, fn: Callable[[K, T], K], /) -> K:
        """Folds every element into an accumulator by applying an operation, returning the final result.

        Example:
        ```python
        res = (
            eater([1, 2, 3])
            .fold("0", lambda acc, x: f"({acc} + {x})")
        )

        print(res)  # (((0 + 1) + 2) + 3)
        ```

        Args:
            init: The initial value.
            fn: The accumlator function.
        """
        while True:
            x = self.next()
            if x.is_none():
                break
            init = fn(init, x._unwrap())

        return init

    def windows(self, size: int) -> "WindowsEaterator[T]":
        """Creates an iterator over overlapping subslices of length `size`.

        Example:
        ```python
        eat = eater([1, 2, 3, 4]).windows(2)

        print(eat.next())  # Some([1, 2])
        print(eat.next())  # Some([2, 3])
        print(eat.next())  # Some([3, 4])
        print(eat.next())  # Option.none()
        ```

        When `size` is greater than the *actual size* of the original iterator, this
        immediately stops.

        ```python
        eat = eater([1, 2, 3]).windows(5)
        print(eat.next())  # Option.none()
        ```
        """
        return WindowsEaterator(self, size)

    def __iter__(self) -> Iterator[T]:
        return self

    # IMPORTANT:
    # Somehow Python executes __len__ when unpacking,
    # which is REALLY bad, since using count() consumes
    # the iterator. Therefore this feature is deprecated
    # for good.

    # def __len__(self) -> int:
    #     return self.count()

    def __next__(self) -> T:
        x = self.next()
        if x.is_some():
            return x._unwrap()
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
                raise ValueError("any of slice(start, stop, step) cannot be negative")

            return self.skip(start).take(stop - start).step_by(step)

    def __repr__(self) -> str:
        return "Eaterator(...)"


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
        return self.__eat.next().map(self.__f)


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


class FlattenEaterator(Eaterator[T]):
    __slots__ = ("__eat", "__cur")

    __eat: Eaterator[AutoIt]
    __cur: Option[Eaterator[T]]

    def __init__(self, eat: Eaterator[AutoIt]):
        self.__eat = eat
        self.__cur = eat.next().map(eater)

    def next(self) -> Option[T]:
        if self.__cur.is_none():
            x = self.__eat.next().map(eater)
            if x.is_none():
                return Option.none()
            self.__cur = x
            return self.next()
        else:
            x = self.__cur._unwrap().next()
            if x.is_none():
                self.__cur = Option.none()
                return self.next()
            else:
                return x


class WindowsEaterator(Eaterator[list[T]]):
    __slots__ = ("__eat", "__d", "__windows")

    __eat: Eaterator[T]
    __d: deque[T]
    __windows: int

    def __init__(self, eat: Eaterator[T], windows: int):
        self.__eat = eat
        self.__d = deque()
        self.__windows = windows

        # prepare the initial state
        for _ in range(windows):
            x = self.__eat.next()
            if x.is_none():
                break

            self.__d.append(x._unwrap())

    def next(self) -> Option[list[T]]:
        if len(self.__d) < self.__windows:
            return Option.none()

        memo = list(self.__d)
        self.__d.popleft()

        x = self.__eat.next()
        if x.is_some():
            self.__d.append(x._unwrap())

        return Option.some(memo)
