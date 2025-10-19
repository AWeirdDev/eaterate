# Custom Eaterator

An `Eaterator` mainly consists of two things:

- `T`: The type of each element.
- `next()`: The function that advances the iterator.

Unlike Python's built-in iterator ecosystem, `eaterate` takes [the Rust approach](https://doc.rust-lang.org/std/iter/trait.Iterator.html), which eliminates the need for raising a `StopIteration` exception everytime an iterator ends.

Every `next()` function override should return an [`Option[T]`](./utilities.md#eaterate.Option), which has two variants, either `Some(...)` (there's data) or `Option.none()` (there's no data, in otherwords, the iterator ended).

Let's say you want to create an iterator that says "chocolate" out loud for `n` times.

```python
from eaterate import Eaterator, Option


class ChocolateEaterator(Eaterator[str]):
    n: int
    
    def __init__(self, n: int):
        self.n = n

    def next(self) -> Option[str]:
        if self.n <= 0:
            return Option.none()
        else:
            self.n -= 1
            return Option.some("chocolate")

# Say, 3 chocolates!
chocolates = ChocolateEaterator(n=3)

print(chocolates.next()) # Some("chocolate")
print(chocolates.next()) # Some("chocolate")
print(chocolates.next()) # Some("chocolate")
print(chocolates.next()) # Option.none()
```

You can also use a `for` block:

```python
for item in chocolates:
    print(item)

# chocolate
# chocolate
# chocolate
```

You can check out the [Core API](./core.md) to see if there's anything cool you'd like to implement. Then, submit your [Pull Request](https://github.com/AWeirdDev/eaterate/pulls) (if you'd like)!

!!! note

    You can also achieve this without writing custom `Eaterator`:

    ```python
    from eaterate import repeat

    chocolates = repeat("chocolate", 3)
    ```
