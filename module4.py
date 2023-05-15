class hashmap:
  def __init__(self,length):
    self.datas = []
    for i in range(length):
      self.datas.append([])

  def append(self, key, value):
    hashed_key = hash(key)
    indice = hashed_key % len(self.datas)
    self.datas[indice].append((key, value))

  def get(self, key):
    hashed_key = hash(key)
    indice = hashed_key % len(self.datas)
    for key_datas, value_datas in self.datas[indice]:
      if key == key_datas:
        return value_datas
    return None