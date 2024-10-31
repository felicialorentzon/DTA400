from math import factorial


def rho(lamb, mu):
    return lamb / mu


def p0(c, lamb, mu):
    result = 0

    for n in range(c):
        result += (rho(lamb, mu) ** n) / factorial(n)

    result += ((rho(lamb, mu)) ** c) / (factorial(c) * (1 - rho(lamb, mu) / c))

    return result ** (-1)


def expected_average_queue_length(c, lamb, mu):
    return (
        p0(c, lamb, mu)
        * ((rho(lamb, mu) ** (c + 1)) / (c * factorial(c)))
        * (1 / ((1 - rho(lamb, mu) / c) ** 2))
    )


def expected_average_number_in_the_systems(c, lamb, mu):
    return expected_average_queue_length(c, lamb, mu) + rho(lamb, mu)


def expected_total_time(c, lamb, mu):
    return expected_average_number_in_the_systems(c, lamb, mu) / lamb


def expected_average_waiting_time(c, lamb, mu):
    return expected_total_time(c, lamb, mu) - 1 / mu


if __name__ == "__main__":
    print("Average time:", expected_average_waiting_time(10, 13, 7.5))
    print("Average length:", expected_average_queue_length(10, 13, 7.5))
