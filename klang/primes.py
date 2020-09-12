"""Prime number utils."""
from typing import Iterator, List


PRIMES: list = [2, 3, 5, 7]
"""Prime number cache."""


def is_prime(number: int) -> bool:
    """Primality test. Check if number is prime.

    Resources:
      - https://en.wikipedia.org/wiki/Primality_test
    """
    if number <= 3:
        return number > 1

    if number % 2 == 0 or number % 3 == 0:
        return False

    i = 5
    while i * i <= number:
        if number % i == 0 or number % (i + 2) == 0:
            return False

        i += 6

    return True


def sieve_of_sundaram(limit: int) -> Iterator[int]:
    """Find all prime numbers up to a limit.

    Args:
        limit: Upper limit.

    Yields:
        Prime numbers.

    Resources:
      - https://en.wikipedia.org/wiki/Sieve_of_Sundaram
      - https://www.geeksforgeeks.org/sieve-sundaram-print-primes-smaller-n/
    """
    half = int((limit - 1) / 2)
    marked = set()
    for i in range(1, half + 1):
        j = i
        while (i + j + 2 * i * j) <= half:
            marked.add(i + j + 2 * i *j)
            j += 1

    if limit >= 2:
        yield 2

    for i in range(1, half + 1):
        if i not in marked:
            yield 2 * i + 1


PRIMES = list(sieve_of_sundaram(10 * 44100))


def _increase_cache(cache: list):
    """Add next prime number to cache.

    Args:
        primes: List of sorted prime numbers.
    """
    if not cache:
        return cache.append(2)

    number = cache[-1] + 1
    if number % 2 == 0:
        number += 1

    while not is_prime(number):
        number += 2

    cache.append(number)


def binary_search_with_upper(array: list, value: int) -> int:
    """Binary search of value in array but returns next bigger value if there is
    no match.

    Args:
        array: Sorted input array to search in.
        value: Target value to look for.

    Returns:
        object: Found or next best target value in array.

    Usage:
        >>> binary_search_with_upper([11, 22, 44], -100)
        11

        >>> binary_search_with_upper([11, 22, 44], 22)
        22

        >>> binary_search_with_upper([11, 22, 44], 23)
        44

        >>> binary_search_with_upper([11, 22, 44], 100)
        ValueError
    """
    if value > array[-1]:
        raise ValueError

    lower = 0
    upper = len(array) - 1
    while lower <= upper:
        mid = (lower + upper) // 2
        if array[mid] == value:
            return array[mid]

        if array[mid] < value:
            lower = mid + 1
        else:
            upper = mid - 1

    return array[lower]


def find_next_prime(number: int) -> int:
    """Find next larger prime for number."""
    global PRIMES
    while number > PRIMES[-1]:
        _increase_cache(PRIMES)

    return binary_search_with_upper(PRIMES, number)


def find_next_primes(nPrimes: int, start: int = 1) -> List[int]:
    """Find the next n prime numbers larger than start."""
    primes = []
    for _ in range(nPrimes):
        primeNr = find_next_prime(start)
        primes.append(primeNr)
        start = primeNr + 1

    return primes
