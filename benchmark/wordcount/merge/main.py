from Store import Store
def main(workflow_name, function_name, request_id, runtime, input, output, to, keys):
    store = Store(workflow_name, function_name, request_id, input, output, to, keys)
    fn = store.fetch(['filename'])['filename']
    keys = ['wordcount_'+f for f in fn]
    counts = store.fetch(keys)

    # merge
    res = {}
    for wc in counts.values():
        for w in wc:
            if w not in res:
                res[w] = wc[w]
            else:
                res[w] += wc[w]

    store.put({'result': res}, {})