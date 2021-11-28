from gevent import monkey
monkey.patch_all()
import uuid
import requests
import getopt
import sys
sys.path.append('..')
from repository import Repository
import config
import pandas as pd
import time
import gevent

repo = Repository()
TEST_PER_WORKFLOW = 3 * 60
e2e_dict = {}

def run_workflow(workflow_name, request_id):
    url = 'http://' + config.GATEWAY_ADDR + '/run'
    data = {'workflow':workflow_name, 'request_id': request_id}
    rep = requests.post(url, json=data)
    return rep.json()['latency']

def analyze_workflow(workflow_name):
    global e2e_dict
    print(f'----analyzing {workflow_name}----')
    total = 0
    start = time.time()
    e2e_total = 0
    while total < 3 or (time.time() - start <= TEST_PER_WORKFLOW and total <= 102):
        total += 1
        id = str(uuid.uuid4())
        print('----firing workflow----', id)
        e2e_latency = run_workflow(workflow_name, id)
        if total > 2:
            e2e_total += e2e_latency
            print('e2e_latency: ', e2e_latency)
    e2e_latency = e2e_total / (total - 2)
    print(f'{workflow_name} e2e_latency: ', e2e_latency)
    e2e_dict[workflow_name] = e2e_latency

def analyze(mode, datamode):
    global e2e_dict
    workflow_pool = ['cycles', 'epigenomics', 'genome', 'soykb', 'video', 'illgal_recognizer', 'fileprocessing', 'wordcount']
    # workflow_pool = ['cycles', 'epigenomics', 'genome', 'soykb']
    # workflow_pool = ['illgal_recognizer']
    if mode == 'single':
        for workflow in workflow_pool:
            analyze_workflow(workflow)
    elif mode == 'corun':
        jobs = []
        for i, workflow_name in enumerate(workflow_pool):
            jobs.append(gevent.spawn_later(i * 3, analyze_workflow, workflow_name))
        gevent.joinall(jobs)
    e2e_latencies = []
    for workflow in workflow_pool:
        e2e_latencies.append(e2e_dict[workflow])
    df = pd.DataFrame({'workflow': workflow_pool, 'e2e_latency': e2e_latencies})
    df.to_csv(f'{datamode}_{mode}.csv')

if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:],'',['mode=', 'datamode='])
    repo.clear_couchdb_results()
    for name, value in opts:
        if name == '--mode':
            mode = value
        elif name == '--datamode':
            datamode = value
    analyze(mode, datamode)