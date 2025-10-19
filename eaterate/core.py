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


class _MISSING: ...


MISSING = _MISSING()


def is_missing(arg: object) -> bool:
    return isinstance(arg, _MISSING)


@overload
def eater(it: "AutoIt[T]", /) -> "Eaterator[T]":
    """Creates an `Eaterator` object from either an iterable, an iterator, or an eaterator.

    - Iterable: something that can create a `Iterator` from `__iter__`.
    - Iterator: something that can be iterated with `__next__`.
    - Eaterator: iterators with additional features.

    Generators are also supported.

    Example:
        ```python
        r = range(100)
        eat: Eaterator = eater(r)
        ```

    Args:
        it (Iterable | Iterator | Eaterator): The iterator or iterable.

    Returns:
        An `Eaterator` (iterator) object.

    Raises:
        TypeError: The provided object is not an iterable, an iterator, or an Eaterator object.
    """


@overload
def eater(fn: Callable[[], T], sentinel: T, /) -> "Eaterator[T]":
    """Creates an `Eaterator` object that keeps calling the `fn` (`fn()`) until the return value
    is equal to the set `sentinel` argument.

    Example:
        ```python
        def maybe_return():
            ...

        eat = eater([1, 2, 3, 4])
        ```

    Args:
        fn: Callable function.
        sentinel: The sentinel (guard).

    Raises:
        TypeError: The provided `fn` is not a callable function.
    """


def eater(
    arg0: Union["AutoIt[T]", Callable[[], T]],
    arg1: Union[T, _MISSING] = MISSING,
    /,
) -> "Eaterator[T]":
    if is_missing(arg1):
        if hasattr(arg0, "__next__"):
            return BuiltinItEaterator(arg0)  # type: ignore
        elif isinstance(arg0, Eaterator):
            return arg0
        elif hasattr(arg0, "__iter__"):
            return BuiltinItEaterator(arg0.__iter__())  # type: ignore
        else:
            raise TypeError(
                f"expected either an iterable, an iterator, or an Eaterator object, got: {type(arg0)!r}"
            )
    else:
        if not hasattr(arg0, "__call__"):
            raise TypeError(
                "expected a callable function for arg0 if `sentinel` is set"
            )
        return CallUntilEaterator(arg0, arg1)  # type: ignore


class CallForNext(Generic[T]):
    __slots__ = ("__eat",)

    __eat: "Eaterator[T]"

    def __init__(self, eat: "Eaterator[T]"):
        self.__eat = eat

    def unwrap(self) -> "Eaterator[T]":
        """Unwraps this object, returning the original iterator.

        Returns:
            Eaterator[T]: The wrapped iterator.
        """
        return self.__eat

    def __call__(self) -> T:
        """Advances the iterator.

        Raises:
            StopIteration: The iterator has ended.
        """
        item = self.__eat.next()
        if item.is_none():
            raise StopIteration

        return item._unwrap()


def call_for_next(it: AutoIt[T]) -> CallForNext[T]:
    """Wraps an iterator in a `CallForNext` object.

    When called, the iterator advances.

    Note that when the iterator ends, a `StopIteration` exception
    is raised.

    Examples:
        ```python
        num = call_for_next([1, 2, 3])
        print(num())  # 1
        print(num())  # 2
        print(num())  # 3
        print(num())  # StopIteration
        ```

    Args:
        it: Either an iterable, an iterator, or an eaterator.
    """
    return CallForNext(eater(it))


class Eaterator(Generic[T]):
    """Iterator with additional features.

    Supports `for` loops.

    Example:
        ```python
        eat = eater([1, 2, 3]).chain([4, 5, 6])
        eat.collect(list)  # [1, 2, 3, 4, 5, 6]
        ```

        You can also use a `for` loop:
        ```python
        eat = eater([1, 2, 3]).chain([4, 5, 6])

        for i in eat:
            print(i)
        ```
    """

    def next(self) -> Option[T]:
        """**Required method**.

        Iterates to the next item.

        On the user's interface, it can also be interpreted as 'the first item' if
        at the start of the iterator.

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

        Returns:
            `Option.none()` if the iteration should stop.
        """
        raise NotImplementedError(
            "`next()` should be implemented.\n"
            "See https://aweirddev.github.io/eaterate/custom for custom iterators."
        )

    def next_chunk(self, n: int, *, strict: bool = False) -> list[T]:
        """Advances the iterator and returns a list containing the next `n` values.

        By default, `strict` is set to `False`, which won't raise an exception.

        Example:
            When `strict` is set to `False` (default behavior), the number of
            elements is less than or equal to `n`.

            ```python
            eat = eater("money ties")

            eat.next_chunk(2)  # ["m", "o"]
            eat.next_chunk(4)  # ["n", "e", "y", " "]
            eat.next_chunk(100)  # ["t", "i", "e", "s"]
            eat.next_chunk(1000)  # []
            ```

            When `strict` is set to `True`, a `ValueError` is raised when the
            number of elements collected for a chunk is not exactly `n`.

            ```python
            eat = eater("money ties")
            eat.next_chunk(2)  # ["m", "o"]
            eat.next_chunk(4)  # ["n", "e", "y", " "]
            eat.next_chunk(100)  # (error) ValueError: expected 100 elements
            ```

        Args:
            n (int): The number of elements.
            strict (bool, optional): When enabled, if the iterator stops before
                collecting exactly `n` items, an exception is raised. Otherwise,
                the returned list might have fewer elements than expected (`<= n`).

        Raises:
            ValueError: The number of elements in a chunk is not exactly `n`.
        """
        if strict:
            arr = []
            i = 0
            for _ in range(n):
                d = self.next()
                if d.is_none():
                    break

                i += 1
                arr.append(d._unwrap())
            else:
                # this is executed when the loop actually finishes
                return arr

            raise ValueError(f"expected {n} items, got {i} items instead")

        else:
            return self.take(n).collect_list()

    def map(self, fn: Callable[[T], K], /) -> "MapEaterator[T, K]":
        """Map the elements of this iterator.

        Example:
            ```python
            eat = (
                eater([1, 2, 3])
                .map(lambda x: str(x * 2))
            )

            print(eat.next())  # Some("2")
            print(eat.next())  # Some("4")
            print(eat.next())  # Some("6")
            print(eat.next())  # Option.none()
            ```

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
            ```
        """
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

        If you'd like to receive more than one element at a time, see :meth:`windows`, which features a more complex implementation.

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

    @overload
    def fold(self, fn: Callable[[K, T], T], init: K, /) -> K:
        """Folds every element into an accumulator by applying an operation, returning the final result.

        Example:
            ```python
            res = (
                eater([1, 2, 3])
                .fold(lambda acc, x: f"({acc} + {x})", "0")
            )

            print(res)  # (((0 + 1) + 2) + 3)
            ```

            ```python
            res = (
                eater([])
                .fold(lambda acc, x: f"({acc} + {x})", "0")
            )

            print(res)  # 0
            ```

        Args:
            fn: The accumlator function.
            init: The initial value.
        """

    @overload
    def fold(self, fn: Callable[[T, T], T], /) -> T:
        """Folds every element into an accumulator by applying an operation, returning the final result.

        For this overload, `init` (the initial value) is not provided, hence the
        first element in this iterator will take its place.

        Example:
            ```python
            import operator

            res = eater([1, 2, 3, 4]).fold(operator.add)
            print(res)  # 10
            ```

        Args:
            fn: The accumulator function.
        """

    def fold(self, fn: Callable[[K, T], K], init: Union[K, _MISSING] = MISSING, /) -> K:
        if is_missing(init):
            init = self.next().unwrap()  # type: ignore

        while True:
            x = self.next()
            if x.is_none():
                break
            init = fn(init, x._unwrap())  # type: ignore

        return init  # type: ignore

    @overload
    def accumulate(
        self, fn: Callable[[K, T], K], init: K, /
    ) -> "AccumulateEaterator[T, K]":
        """Make an iterator that returns accumulated results for every element.

        See `fold()` if you'd like a singular return value.

        Example:
            ```python
            def better(acc: str, current: str) -> str:
                return f"{current} is better than {acc}"

            eat = (
                eater(["fruit", "chocolate"])
                .accumulate(better, "nothing")
            )

            print(eat.next())
            # Some("fruit is better than nothing")

            print(eat.next())
            # Some("chocolate is better than fruit is better than nothing")

            print(eat.next())
            # Option.none()
            ```
        """

    @overload
    def accumulate(self, fn: Callable[[T, T], T], /) -> "AccumulateEaterator[T, T]":
        """Make an iterator that returns accumulated results for every element.

        For this overload, `init` (the initial value) is not provided, hence the
        first element in this iterator will take its place.

        See `fold()` if you'd like a singular return value.

        Example:
            To calculate sum:

            ```python
            import operator

            eat = (
                eater([1, 2, 3, 4])
                .accumulate(operator.add)
            )

            # operator.add(1, 2) = 3
            print(eat.next())  # Some(3)

            # operator.add(3, 3) = 6
            print(eat.next())  # Some(6)

            # operator.add(6, 4) = 10
            print(eat.next())  # Some(10)

            print(eat.next())  # Option.none()
            ```

            To find the maximum value:

            ```python
            eat = (
                eater([-2, 10, 5, 20])
                .accumulate(max)
            )

            # max(-2, 10) = 10
            print(eat.next())  # Some(10)

            # max(10, 5) = 10
            print(eat.next())  # Some(10)

            # max(5, 20) = 20
            print(eat.next())  # Some(20)

            print(eat.next())  # Option.none()
            ```
        """

    def accumulate(
        self, fn: Callable[[K, T], K], init: Union[K, _MISSING] = MISSING, /
    ) -> "AccumulateEaterator[T, K]":
        if is_missing(init):
            return AccumulateEaterator(self, self.next().unwrap(), fn)  # type: ignore
        else:
            return AccumulateEaterator(self, init, fn)  # type: ignore

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

    def procedural(self) -> "CallForNext[T]":
        """Wraps this iterator in a `CallForNext` object.

        When called, the iterator advances.

        Note that when the iterator ends, a `StopIteration` exception
        is raised.

        Examples:
            ```python
            num = eater([1, 2, 3]).procedural()
            print(num())  # 1
            print(num())  # 2
            print(num())  # 3
            print(num())  # (error) StopIteration
            ```

            To get back to `Eaterator`, use `unwrap()`:
            ```python
            num = eater([1, 2, 3]).procedural()
            print(num())  # 1

            num = num.unwrap()
            print(num.next())  # Some(2)
            print(num.next())  # Some(3)
            print(num.next())  # Option.none()
            ```

        Returns:
            CallForNext[T]: The wrapper.
        """
        return CallForNext(self)

    def to_iter(self) -> Iterator[T]:
        """Converts back to Python's built-in iterator."""
        # yeah they won't notice lol
        return self.__iter__()

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


class CallUntilEaterator(Eaterator[T]):
    __slots__ = ("__f", "__sentinel")

    __f: Callable[[], T]
    __sentinel: T

    def __init__(self, f: Callable[[], T], s: T):
        self.__f = f
        self.__sentinel = s

    def next(self) -> Option[T]:
        r = self.__f()
        if r == self.__sentinel:
            return Option.none()
        else:
            return Option.some(r)


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


class AccumulateEaterator(Generic[T, K], Eaterator[K]):
    __slots__ = ("__eat", "__f", "__d")

    __eat: Eaterator[T]
    __f: Callable[[K, T], K]
    __d: K

    def __init__(self, eat: Eaterator[T], init: K, f: Callable[[K, T], K]):
        self.__eat = eat
        self.__f = f
        self.__d = init

    def next(self) -> Option[K]:
        item = self.__eat.next()
        if item.is_none():
            return Option.none()

        self.__d = self.__f(self.__d, item._unwrap())
        return Option.some(self.__d)
