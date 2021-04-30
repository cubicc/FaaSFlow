import parser
import queue
import json
import repository

inter_communication_time = 0.1
node_cnt = 10
node_ip = ['', '', '', '', '', '', '', '', '', '']


def init_graph(workflow, group_set):
    in_degree_vec = dict()
    q = queue.Queue()
    q.put(workflow.start)
    group_set.append({workflow.start.name})
    while q.empty() is False:
        node = q.get()
        for next_node_name in node.next:
            if next_node_name not in in_degree_vec:
                in_degree_vec[next_node_name] = 1
                q.put(workflow.nodes[next_node_name])
                group_set.append({next_node_name})
            else:
                in_degree_vec[next_node_name] += 1
    return in_degree_vec


def find_set(node, group_set):
    for node_set in group_set:
        if node in node_set:
            return node_set
    return None


def topo_search(workflow, in_degree_vec, group_set, no_net_latency):
    dist_vec = dict()  # { name: [dist, max_length] }
    prev_vec = dict()  # { name: [prev_name, length] }
    q = queue.Queue()
    q.put(workflow.start)
    dist_vec[workflow.start.name] = [workflow.start.runtime, 0]
    prev_vec[workflow.start.name] = []
    while q.empty() is False:
        node = q.get()
        pre_dist = dist_vec[node.name]
        prev_name = node.name
        for index in range(len(node.next)):
            next_node = workflow.nodes[node.next[index]]
            w = node.nextDis[index]
            next_node_name = next_node.name
            if no_net_latency is True:
                w = 0
            elif next_node_name in find_set(prev_name, group_set):
                w = inter_communication_time
            if next_node.name not in dist_vec:
                dist_vec[next_node_name] = [pre_dist[0] + w + next_node.runtime, max(pre_dist[1], w)]
                prev_vec[next_node_name] = [prev_name, w]
            elif dist_vec[next_node_name][0] < pre_dist[0] + w + next_node.runtime:
                dist_vec[next_node_name] = [pre_dist[0] + w + next_node.runtime, max(pre_dist[1], w)]
                prev_vec[next_node_name] = [prev_name, w]
            elif dist_vec[next_node_name][0] == pre_dist[0] + w + next_node.runtime and max(pre_dist[1], w) > \
                    dist_vec[next_node_name][1]:
                dist_vec[next_node_name][1] = max(pre_dist[1], w)
                prev_vec[next_node_name] = [prev_name, w]
            in_degree_vec[next_node_name] -= 1
            if in_degree_vec[next_node_name] == 0:
                q.put(next_node)
    return dist_vec, prev_vec


def mergeable(node1, node2, group_set, group_size):
    node_set1 = find_set(node1, group_set)
    if node2 in node_set1:
        return False
    node_set2 = find_set(node2, group_set)
    if len(node_set1) + len(node_set2) > group_size:
        return False
    group_set.remove(node_set1)
    group_set.remove(node_set2)
    group_set.append(node_set1 | node_set2)
    return True


penalty_rate = 1.5


def merge_node(crit_vec, group_set, group_size):
    merge_flag = False
    for edge in crit_vec:
        merge_flag = merge_flag | mergeable(edge[0], edge[1][0], group_set, group_size)
        if merge_flag:
            break
    return merge_flag


def get_longest_dis(workflow, dist_vec):
    dist = 0
    node_name = ''
    for node in workflow.nodes:
        if dist_vec[node.name][0] > dist:
            dist = dist_vec[node.name][0]
            node_name = node.name
    return dist, node_name


def grouping(workflow):
    topo_search_cnt = 0
    group_set = list()
    in_degree_vec = init_graph(workflow, group_set)
    group_size = 1
    total_node_cnt = len(workflow.nodes)
    no_latency_dist_vec, _ = topo_search(workflow, in_degree_vec.copy(), group_set, True)
    # no_latency_crit_length = no_latency_dist_vec[workflow.end.name][0]
    no_latency_crit_length, _ = get_longest_dis(workflow, no_latency_dist_vec)
    init_flag = True
    init_crit_length = 0

    while True:
        dist_vec, prev_vec = topo_search(workflow, in_degree_vec.copy(), group_set, False)
        topo_search_cnt = topo_search_cnt + 1
        # crit_length = dist_vec[workflow.end.name][0]
        crit_length, tmp_node_name = get_longest_dis(workflow, dist_vec)
        print('crit_length: ', crit_length)
        print('barrier: ', no_latency_crit_length * penalty_rate)
        if init_flag:
            init_crit_length = crit_length
            init_flag = False
        if crit_length < no_latency_crit_length * penalty_rate:
            break
        elif group_size == total_node_cnt:
            break
        crit_vec = dict()
        while tmp_node_name != workflow.start.name:
            crit_vec[tmp_node_name] = prev_vec[tmp_node_name]
            tmp_node_name = prev_vec[tmp_node_name][0]
        crit_vec = sorted(crit_vec.items(), key=lambda c: c[1][1], reverse=True)
        if not merge_node(crit_vec, group_set, group_size):
            group_size = group_size + 1
            merge_node(crit_vec, group_set, group_size)
    print(init_crit_length, crit_length, no_latency_crit_length)
    print(group_size)
    return group_set


def get_type(name, node, group_detail, mode):
    if mode == 'input':
        for prev_node in node.prev:
            if name in prev_node.output_files:
                node_set = find_set(prev_node.name, group_detail)
                return 'MEM' if node.name in node_set else 'DB'
        return 'DB'
    else:
        not_in_same_set = False
        in_same_set = False
        for next_node in node.next:
            if name in next_node.input_files:
                node_set = find_set(next_node.name, group_detail)
                if node.name not in node_set:
                    not_in_same_set = True
                else:
                    in_same_set = True
        if not_in_same_set and in_same_set:
            return 'DB+MEM'
        elif in_same_set:
            return 'MEM'
        else:
            return 'DB'


def save_function_info():
    group_detail = grouping(parser.workflow)
    function_info_list = list()
    function_info_list_raw = list()
    for node_name in parser.workflow.nodes:
        node = parser.workflow.nodes[node_name]
        function_info = {'function_name': node.name, 'runtime': node.runtime,
                         'parent_cnt': parser.workflow.parent_cnt[node.name], 'conditions': node.conditions}
        function_info_raw = {'function_name': node.name, 'runtime': node.runtime,
                             'parent_cnt': parser.workflow.parent_cnt[node.name], 'conditions': node.conditions}
        function_input = list()
        function_input_raw = list()
        for input_file in node.input_files:
            function_input.append({'type': get_type(input_file, node, group_detail, 'input'),
                                   'size': input_file['size'],
                                   'function': input_file['function'],
                                   'parameter': input_file['parameter']})
            function_input_raw.append({'type': 'DB', 'size': input_file['size'],
                                       'function': input_file['function'], 'parameter': input_file['parameter']})
        function_output = list()
        function_output_raw = list()
        for output_file in node.output_files:
            function_output.append({'type': get_type(output_file, node, group_detail, 'output'),
                                    'size': output_file['size'],
                                    'function': output_file['function'],
                                    'parameter': output_file['parameter']})
            function_output_raw.append({'type': 'DB', 'size': output_file['size'],
                                        'function': output_file['function'], 'parameter': output_file['parameter']})
        function_info['input'] = function_input
        function_info['output'] = function_output
        function_info['next'] = node.next
        function_info_raw['input'] = function_input_raw
        function_info_raw['output'] = function_output_raw
        function_info_raw['next'] = node.next
        function_info_list.append(function_info)
        function_info_list_raw.append(function_info_raw)
    return function_info_list, function_info_list_raw


info_list, info_list_raw = save_function_info()
repository.save_function_info(info_list, 'function_info')
repository.save_start_node_name(parser.workflow.start.name, 'function_info')
repository.save_function_info(info_list_raw, 'function_info_raw')
repository.save_start_node_name(parser.workflow.start.name, 'function_info_raw')
repository.save_basic_input(parser.workflow.global_input)
