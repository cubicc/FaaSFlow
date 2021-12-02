# FaaSFlow

## Introduction

FaaSFlow is a serverless workflow engine that enables efficient workflow execution in 2 ways: a worker-side workflow schedule pattern to reduce scheduling overhead, and a adaptive storage library to use local memory to transfer data between functions on the same node.

## Hardware Depedencies and Private IP Address

1. In our experiment setup, we use aliyun ecs instance installed with Ubuntu 18.04 (ecs.g7.2xlarge, cores: 8, DRAM: 32GB) for each worker node, and a ecs.g6e.4xlarge(cores: 16, DRAM: 64GB) instance for database node installed with Ubuntu 18.04 and CouchDB.

2. Please save the private IP address of the storage node as the **<master_ip>**, and save the private IP addredd of other 7 worker nodes as the **<worker_ip>**. 

## Installation and Software Dependencies

Clone our code `https://github.com/lzjzx1122/FaaSFlow.git` and:

1. Reset `worker_address` configuration with your <worker_ip>:8000 on `src/grouping/node_info.yaml`. It will specify your worker address. The `scale_limit: 120` respresents the maximum container numbers that can be deployed in each 32GB memory instance, and it do not need any change by default.

2. Reset `COUCHDB_URL` as `http://openwhisk:openwhisk@<master_ip>:5984/`  in `src/container/config.py`, `src/workflow_manager/config.py`, `test/asplos/config.py`. It will specify the corresponding database storage you build previously.

3. Then, clone the modified code into each node (8 nodes total).

4. On the storage node: Run `scripts/db_setup.bash`. This install docker, couchdb, some python packages, and build grouping results from 8 benchmarks.

5. On each worker node: Run `scripts/worker_setup.bash`. This install docker, redis, some python packages, and build docker images from 8 benchmarks.

## WorkerSP Start-up

The following operations help to run scripts under WorkerSP. Firstly, enter `src/workflow_manager`, change the configuration by `DATA_MODE = optimized` and `CONTROL_MODE = WorkerSP` in both 7 worker nodes and storage node. Then, start the engine proxy with the local  <worker_ip> on each worker node by the following <span id="jump">command</span>: 
```
    python3 proxy.py <worker_ip> 8000             (proxy start)
```
Enter `test/asplos/config.py` and define the `GATEWAY_ADDR` as `<master_ip>:7000`. Then start the gateway on the storage node by the following command: 
```
    python3 gateway.py <master_ip> 7000           (gateway start)
``` 
If you would like to run scripts under WorkerSP, you have finished all the operations and allowed to send invocations **by `run.py` scripts for all WorkerSP-based performance test**. Detailed scripts usage is introduced in [Run Experiment](#jumpexper).
    
**Note:** We recommend to restart the `proxy.py` on each worker node and the `gateway.py` on the master node whenever you start the `run.py` script, to avoid any potential bugs.

## MasterSP Start-up

The following operations help to run scripts under MasterSP. Firstly, enter `src/workflow_manager`, change the configuration by `DATA_MODE = raw` and `CONTROL_MODE = MasterSP` in both 7 worker nodes and storage node. Then, restart the engine proxy on each worker node by the [proxy start](#jump) command, and restart the gateway on the storage node by the [gateway start](#jump) command.

Enter `src/workflow_manager/config.py`, and define the `MASTER_HOST` as `<master_ip>:8000`. Then,
start another proxy at the storage node as the virtual master node by the following command: 
```
    python3 proxy.py <master_ip> 8000
```
If you would like to run scripts under MasterSP, you have finished all the operations and allowed to send invocations **by `run.py` scripts for all Master-based performance test**. Detailed scripts usage is introduced in [Run Experiment](#jumpexper).

## <span id="jumpexper">Run Experiment</span>

We provide some test scripts under `test/asplos`.
**<span id="note">Note:**</span> We recommend to restart all `proxy.py` and `gateway.py` processes whenever you start the `run.py` script, to avoid any potential bugs. The restart will clear all background function containers and reclaim the memory space. 

### Scheduler Scalability: the overhead of graph scheduler when scale-up total nodes of one workflow

Directly run on the storage node: 
```
    python3 run.py
```

### Component Overhead: overhead of one workflow engine

Start a proxy at any worker node (skip if you have already done in the above start-up) and get its pid. Then run it on any worker node:
```
    python3 run.py --pid=<pid>
```
    
### Data Overhead: total time spend on data transmission

Make the WorkerSP deployment, run it on the storage node: 
```
    python3 run.py --datamode=optimized
```

Then make the MasterSP deployment, run it again with `--datamode=raw`.

### End-to-End Latency: run one-by-one and run all-at-once

Firstly, Make the WorkerSP deployment, run it on the storage node: 
```
    python3 run.py --datamode=optimized --mode=single
```
Then terminate and restart all `proxy.py` and `gateway.py` (reasons in [here](#note)), run it again with `--datamode=optimized --mode=corun`.

Secondly, make the MasterSP deployment, run it on the storage node:
```
    python3 run.py --datamode=raw --mode=single
```
Then terminate and restart all `proxy.py` and `gateway.py` , run it again with `--datamode=raw --mode=corun`.

### Schedule Overhead: time spend on scheduling tasks

Make the WorkerSP deployment, run it on the storage node: 
```
    python3 run.py --controlmode=WorkerSP
```
Then make the MasterSP deployment, run it again with `--controlmode=MasterSP`.


### 99%-ile latency at 50MB/s, 6 request/min for all benchmark

1. Download wondershaper at `https://github.com/magnific0/wondershaper` to the storage node.

2. Make the WorkerSP deployment, and run the following commands in your storage node. These will clear the previous bandwidth setting and set the network bandwidth to 50MB/s:
```
    cd <your_wondershaper_path>/wondershaper
    ./wondershaper -a docker0 -c
    ./wondershaper -a docker0 -u 409600 -d 409600
```
3. Then run the script on the storage node:
```
    python3 run.py --datamode=optimized
```

4. Make the MasterSP deployment, run it again with `--datamode=raw`


### 99%-ile latency at from 25MB/s-100MB/s, and with dfferent request/min for benchmark genome and video

1. Make the WorkerSP deployment, and run the following commands in your storage node. These will clear the previous bandwidth setting and set the network bandwidth to 25MB/s:
```
    cd <your_wondershaper_path>/wondershaper
    ./wondershaper -a docker0 -c
    ./wondershaper -a docker0 -u 204800 -d 204800
```
and then run the following commands on the storage node. 
**Remember to restart all `proxy.py` and the `gateway.py` whenever you start the `run.py` script, to avoid any potential bugs.**

```
python3 run.py --bandwidth=25 --datamode=optimized --workflow=genome    
```


2. clear the previous bandwidth setting and set the network bandwidth to 50MB/s:
```
    cd <your_wondershaper_path>/wondershaper
    ./wondershaper -a docker0 -c
    ./wondershaper -a docker0 -u 409600 -d 409600
```
and then run the following commands on the storage node.
```
    python3 run.py --bandwidth=50 --datamode=optimized --workflow=genome    
```
3. Other configurations follow the same logic (`-u 614400 -d 614400` and `--bandwidth=75` corresponds to 75MB/s, `-u 819200 -d 819200` and `--bandwidth=100` corresponds to 100MB/s)

4. Make the MasterSP deployment, review the step 1 and 2, however with `--datamode=raw`. The evaluation of benchmark follows the same logic with `--workflow=video`.
