# Création de l'arbre de conversation
class Node:
    def __init__(self, answer_to_go_here, question):
        self.answer_to_go_here = answer_to_go_here
        self.question = question
        self.next_nodes = []

    def size(self):
        count = 1 
        for node in self.next_nodes:
            count += node.size()  
        return count

    def depth(self):
        Max = 0
        for node in self.next_nodes:
            if node.depth() > Max:
                Max = node.depth()
        return Max + 1

    def append(self, question, reponses, question_precedante):
        if question_precedante == self.question:
            self.next_nodes.append(Node(question, reponses))
        for n in self.next_nodes:
            n.append(question, reponses, question_precedante)

class Tree:
    def __init__(self, question):
        self.first_node = Node("", question)
        self.current_node = self.first_node

    def size(self):
        return self.first_node.size()

    def depth(self):
        return self.first_node.depth()

    def append(self, question, reponses, question_precedante):
        self.first_node.append(question, reponses, question_precedante)

    def get_question(self):
        return self.current_node.question

    def choose(self, message):
        for i in range(len(self.current_node.next_nodes)):
            if message.content.lower() in self.current_node.next_nodes[i].answer_to_go_here:
                self.current_node = self.current_node.next_nodes[i]
                return True
        return False

    def reset(self):
        self.current_node = self.first_node