import time


def benchmark(func):
    def function_timer(*args, **kwargs):
        start = time.time()
        value = func(*args, **kwargs)
        end = time.time()
        runtime = end - start

        print('Runtime benchmark: ' + func.__name__ + ' took ' + str(runtime) + ' seconds.')

        return value

    # Make sure you don't use parens when returning the above function
    # You're only returning a reference by the name of the function
    return function_timer


