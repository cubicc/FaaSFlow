import random
from Store import Store


def main(function_name, request_id, runtime, input, output, foreach_id):
    store = Store(function_name, request_id)
    param = store.fetch(input, foreach_id)

    count = int(param['count'])

    array = []
    for _ in range(count):
        array.append(random.randrange(0, 10))

    res = {'rand_result': array}

    store.put(output, res, foreach_id)
