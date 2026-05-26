from dataclasses import dataclass, field
from typing import Any, List, Optional
from collections import deque


@dataclass
class GraphNode:
    id: str
    data: Any = None


@dataclass
class GraphEdge:
    source: str
    target: str


class Graph:
    def __init__(self):
        self.nodes: List[GraphNode] = []
        self.edges: List[GraphEdge] = []

    def add_node(self, node_id: str, data: Any = None) -> None:
        if self.get_node(node_id) is not None:
            return
        self.nodes.append(GraphNode(id=node_id, data=data))

    def remove_node(self, node_id: str) -> None:
        self.nodes = [n for n in self.nodes if n.id != node_id]
        self.edges = [e for e in self.edges if e.source != node_id and e.target != node_id]

    def add_edge(self, source: str, target: str) -> None:
        for e in self.edges:
            if e.source == source and e.target == target:
                return
        self.edges.append(GraphEdge(source=source, target=target))

    def remove_edge(self, source: str, target: str) -> None:
        self.edges = [e for e in self.edges if not (e.source == source and e.target == target)]

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        for n in self.nodes:
            if n.id == node_id:
                return n
        return None

    def get_successors(self, node_id: str) -> List[str]:
        return [e.target for e in self.edges if e.source == node_id]

    def get_predecessors(self, node_id: str) -> List[str]:
        return [e.source for e in self.edges if e.target == node_id]

    def get_in_degree(self, node_id: str) -> int:
        return sum(1 for e in self.edges if e.target == node_id)

    def get_out_degree(self, node_id: str) -> int:
        return sum(1 for e in self.edges if e.source == node_id)


def topological_sort(graph: Graph) -> List[str]:
    in_degree = {n.id: 0 for n in graph.nodes}
    for edge in graph.edges:
        if edge.target in in_degree:
            in_degree[edge.target] += 1

    queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
    result = []

    while queue:
        node_id = queue.popleft()
        result.append(node_id)
        for succ in graph.get_successors(node_id):
            if succ in in_degree:
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)

    if len(result) != len(graph.nodes):
        raise ValueError("图中存在环，无法进行拓扑排序")

    return result


def has_cycle(graph: Graph) -> bool:
    WHITE = 0
    GRAY = 1
    BLACK = 2

    color = {n.id: WHITE for n in graph.nodes}
    adj = {n.id: graph.get_successors(n.id) for n in graph.nodes}

    def dfs(node_id: str) -> bool:
        color[node_id] = GRAY
        for neighbor in adj[node_id]:
            if neighbor not in color:
                continue
            if color[neighbor] == GRAY:
                return True
            if color[neighbor] == WHITE and dfs(neighbor):
                return True
        color[node_id] = BLACK
        return False

    for node in graph.nodes:
        if color[node.id] == WHITE:
            if dfs(node.id):
                return True
    return False


def has_multiple_endpoints(graph: Graph) -> bool:
    endpoints = [n.id for n in graph.nodes if graph.get_out_degree(n.id) == 0]
    return len(endpoints) > 1


def build_graph_from_route_design(route_design: dict) -> Graph:
    graph = Graph()
    for node_data in route_design.get("nodes", []):
        node_id = node_data["id"]
        data = node_data.get("data")
        graph.add_node(node_id, data)
    for edge_data in route_design.get("edges", []):
        source = edge_data["source"]
        target = edge_data["target"]
        graph.add_edge(source, target)
    return graph
