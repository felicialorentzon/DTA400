from math import factorial


def rho(c, lamb, mu):
    return lamb / (c * mu)


def pi0(c, lamb, mu):
    result = 0
    for k in range(c):
        result += ((c * rho(c, lamb, mu)) ** k) / factorial(k)
    result += (
        ((c * rho(c, lamb, mu)) ** c) / factorial(c) * (1 / (1 - rho(c, lamb, mu)))
    )
    return result


def C(c, lamb, mu):
    intermediate = 0
    for k in range(c):
        intermediate += ((c * rho(c, lamb, mu)) ** k) / factorial(k)
    return 1 / (
        1
        + (1 - rho(c, lamb, mu))
        * (factorial(c) / ((c * rho(c, lamb, mu) ** c) * intermediate))
    )


def average(c, lamb, mu):
    return rho(c, lamb, mu) / (1 - rho(c, lamb, mu)) * C(c, lamb, mu) + c * rho(
        c, lamb, mu
    )


def customers_in_queue(c, lamb, mu):
    return rho(c, lamb, mu) / (1 - rho(c, lamb, mu)) * C(c, lamb, mu)


if __name__ == "__main__":
    print(average(20, 30, 7.5))
    print(customers_in_queue(20, 30, 7.5))
