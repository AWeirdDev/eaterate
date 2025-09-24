from collections import deque
from eaterate import eater, erange

eat = (
    erange(0, ..., 20)
    .map(chr)
    .take(10)
    .intersperse("bruh")
    .filter(lambda x: x == "bruh")
    .collect_deque(reverse=False)
)

print(len(eat))
