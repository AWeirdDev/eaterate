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

print(chocolates.next())  # Some("chocolate")
print(chocolates.next())  # Some("chocolate")
print(chocolates.next())  # Some("chocolate")
print(chocolates.next())  # Option.none()
