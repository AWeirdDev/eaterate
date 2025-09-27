# Eaterate

Eaterate *(eet-uh-rate)* is a toolkit of modern Python iterators. Or whatever the hell you wanna call this.

**Key features**:

- **Fully typed**. C'mon, type annotations are just essential these days.

```python
from eaterate import eater

eat = eater("hi!").enumerate()

for index, char in eat:
    print(index, char)

# Output:
# 0 h
# 1 i
# 2 !
```

## Quick tour
With `eaterate`, you can use iterators in the easiest way possible:

```python
eat = (
    eater([1, 2])
    .chain([4, 5])
    .map(lambda i: i * 2)
)

# collects to a list
print(eat.collect(list))

# [2, 4, 8, 10]
```

You can also add separators to your iterator like never before (kind of):

```python
eat = eater([1, 2, 3]).intersperse(500)
for i in eat:
    print(i)

# Output:
# 1
# 500
# 2
# 500
# 3
```

There are a lot of more features to try out! Refer to the [Core API](./core.md) reference for more!

## Architecture

Instead of raising `StopIteration` (exception-like) when an iterator ends, `eaterate` uses value wrappers, specifically [`Option[T]`](./utilities.md#eaterate.Option).
