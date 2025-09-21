# eaterate
Modern Python iterators. With a Rust-like syntax, hell nawh.

```python
from eaterate import eater

eat = eater("hi!").chain("yes")

for c in eat:
    print(c)

# Output:
# h
# i
# !
# y
# e
# s
```
