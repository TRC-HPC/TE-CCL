from teccl.input_data import TopologyParams
from teccl.topologies.topology import Topology


class A2(Topology):
    def __init__(self, topo_input: TopologyParams):
        super().__init__(topo_input)

    def construct_topology(self, topo_input: TopologyParams):
        #self.node_per_chassis = self.side_length ** 2

        rate = 200 / self.chunk_size

        self.capacity = [[0 for _ in range(261)] for _ in range(261)]
        self.alpha = [[0 for _ in range(261)] for _ in range(261)]

        for switch in range(4):
            self.capacity[256 + switch][260] = rate * 64
            self.alpha[256 + switch][260] = 1e-6

            for gpu in range(64):
                self.capacity[switch * 64 + gpu][256 + switch] = rate
            
        for i in range(256):
            for j in range(256):
                if i != j and i // 8 == j // 8:
                    self.capacity[i][j] = 2 * rate
                    self.alpha[i][j] = 1e-7    

        for i in range(261):
            for j in range(261):
                self.capacity[i][j] = max(self.capacity[i][j],self.capacity[j][i])
                self.capacity[j][i] = max(self.capacity[i][j],self.capacity[j][i])
                self.alpha[j][i] = max(self.alpha[i][j],self.alpha[j][i])
                self.alpha[i][j] = max(self.alpha[i][j],self.alpha[j][i])
        

        self.switch_indices = [256,257,258,259,260]
    
        print(self.capacity[0])
        print(self.capacity[257])
    def set_switch_indicies(self) -> None:
        super().set_switch_indicies()