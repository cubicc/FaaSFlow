class ServerlessBase(object):
    def __init__(self, objType, name, next):
        self.name = name
        self.next = next
        self.prev = []
        # self.prev_queue = []
        self.prev_set = []
        self.father = None
        self.type = objType