class node:
  def __init__(self,data):
    self.data = data
    self.next_node = None

class queue:
  def __init__(self, data):
    self.first_node = node(data)

  def pop(self):
    if self.first_node == None:
      return

    data = self.first_node.data
    self.first_node = self.first_node.next_node
    return data

  def append(self,data):
    current_node = self.first_node
    while current_node.next_node != None:
      current_node = current_node.next_node
    current_node.next_node = node(data)