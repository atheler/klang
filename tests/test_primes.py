import unittest

from klang.primes import is_prime, sieve_of_sundaram, _increase_cache, find_next_prime


class TestPrimes(unittest.TestCase):

    PRIMES_UNDER_100 = [
        2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67,
        71, 73, 79, 83, 89, 97,
    ]

    def test_is_prime(self):
        for number in range(-10, 100):
            if number in self.PRIMES_UNDER_100:
                self.assertTrue(is_prime(number))
            else:
                self.assertFalse(is_prime(number))

    def test_sieve_of_sundaram(self):
        self.assertEqual(list(sieve_of_sundaram(1)), [])
        self.assertEqual(list(sieve_of_sundaram(2)), [2])
        self.assertEqual(list(sieve_of_sundaram(3)), [2, 3])
        self.assertEqual(list(sieve_of_sundaram(100)), self.PRIMES_UNDER_100)

    def test_increase_cache(self):
        cache = []

        _increase_cache(cache)

        self.assertEqual(cache, [2])

        _increase_cache(cache)

        self.assertEqual(cache, [2, 3])

        _increase_cache(cache)

        self.assertEqual(cache, [2, 3, 5])

        _increase_cache(cache)

        self.assertEqual(cache, [2, 3, 5, 7])

    def test_find_next_prime(self):
        primes = iter(self.PRIMES_UNDER_100)
        nextPrime = next(primes)
        for number in range(-10, 97):
            self.assertEqual(find_next_prime(number), nextPrime)
            if number == nextPrime:
                nextPrime = next(primes)


if __name__ == '__main__':
    unittest.main()

