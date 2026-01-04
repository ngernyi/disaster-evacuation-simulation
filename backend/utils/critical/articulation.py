import networkx as nx

G = nx.Graph()

# Add all the networks


critical_nodes = nx.articulation_points(G)

