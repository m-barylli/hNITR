# %%
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from diffupy.diffuse import run_diffusion_algorithm
from diffupy.matrix import Matrix
from diffupy.diffuse_raw import diffuse_raw
from diffupy.kernels import regularised_laplacian_kernel, diffusion_kernel
import random

# %%
# switch matplotlib background to dark mode
plt.style.use('dark_background')

# %%
TRRUST_df = pd.read_csv('/home/celeroid/Documents/CLS_MSc/Thesis/EcoCancer/MONIKA/data/TRRUSTv2/trrust_rawdata.human.tsv', sep='\t')
data_proteins = pd.read_csv('/home/celeroid/Documents/CLS_MSc/Thesis/EcoCancer/MONIKA/Diffusion/data/proteomics_for_pig_cmsALL.csv')
data_RNA = pd.read_csv('/home/celeroid/Documents/CLS_MSc/Thesis/EcoCancer/MONIKA/Diffusion/data/transcriptomics_for_pig_cmsALL.csv')

data_proteins = data_proteins.columns
data_RNA = data_RNA.columns

#tf_proteins is the first column of tf_bs_proteins
tf_proteins = TRRUST_df.iloc[:,0].unique()

# check overlap
prot_tfs = np.intersect1d(data_proteins, tf_proteins)
print(f'Number of TFs in sample: {len(prot_tfs)}')

rna_tfs = np.intersect1d(data_RNA, prot_tfs)
print(f'Number of TF mRNAs: {len(rna_tfs)}')

# incex tf_bs_proteins at prot_tfs
TRRUST_df = TRRUST_df[TRRUST_df.iloc[:,0].isin(prot_tfs)]
tf_targets_db = TRRUST_df.iloc[:,1].unique()

targeted_RNA = np.intersect1d(tf_targets_db, data_RNA)
print(f'Number of targeted RNA: {len(targeted_RNA)}')

targeted_PROTS = np.intersect1d(targeted_RNA, data_proteins)
print(f'Proteins encoded by targeted RNA:  {len(targeted_PROTS)}')

DEA_PROTS_CMS4 = pd.read_csv('/home/celeroid/Documents/CLS_MSc/Thesis/EcoCancer/MONIKA/Diffusion/data/Synapse/TCGA/Proteomics_CMS_groups/top_100_CMS4_PROT.csv')
DEA_RNA = pd.read_csv('/home/celeroid/Documents/CLS_MSc/Thesis/EcoCancer/MONIKA/Diffusion/data/Synapse/TCGA/RNA_CMS_groups/top100_RNA_CMS4.csv')

# # check overlap between DEA_PROTS_CMS4 and targeted_PROTS
# DEA_PROTS_CMS4 = DEA_PROTS_CMS4.to_numpy()
# DEA_targeted_PROTS = np.intersect1d(DEA_PROTS_CMS4, targeted_PROTS)
# print(f'Top {len(DEA_PROTS_CMS4)} DEA proteins in targeted_PROTS: {len(DEA_targeted_PROTS)}')

# # check overlap between DEA_PROTS_CMS4 and prot_tfs
# DEA_TF_PROTS = np.intersect1d(DEA_PROTS_CMS4, prot_tfs)
# print(f'Top {len(DEA_PROTS_CMS4)} DEA proteins in prot_tfs: {len(DEA_TF_PROTS)}')
# print(f'RNA coding for Top DEA TF: {np.intersect1d(DEA_TF_PROTS, rna_tfs)}\n')


# concatenate prot_tfs and  targeted_PROTS
all_PROTS = list(set(np.concatenate((prot_tfs, targeted_PROTS))))
print(f'Total number of scaffold proteins (Before STRING expansion): {len(all_PROTS)}')



# # write to csv
# pd.DataFrame(all_PROTS).to_csv('/home/celeroid/Documents/CLS_MSc/Thesis/EcoCancer/MONIKA/Diffusion/data/all_TRRUST_prots.csv', index=False)


# %%
# Filter the TRRUST entries
# Check if entries in the first column of tfs_and_targets are in the first column of prot_tfs
condition1 = TRRUST_df['TF_PROT'].isin(prot_tfs)
# Check if entries in the second column of tfs_and_targets are in the second column of targeted_RNA
condition2 = TRRUST_df['BS_RNA'].isin(targeted_RNA)

# Filter tfs_and_targets where both conditions are true
TRRUST_df = TRRUST_df[condition1 & condition2]

def bs_to_bs_prot(bs_value):
    return bs_value if bs_value in targeted_PROTS else np.nan

def tf_prot_to_tf_rna(tf_prot_value):
    return tf_prot_value if tf_prot_value in rna_tfs else np.nan

TRRUST_df['BS_PROT'] = TRRUST_df['BS_RNA'].apply(bs_to_bs_prot)

TRRUST_df['TF_RNA'] = TRRUST_df['TF_PROT'].apply(tf_prot_to_tf_rna)

# place the TF_RNA column before the TF column
cols = TRRUST_df.columns.tolist()
cols = cols[-1:] + cols[:-1]

TRRUST_df = TRRUST_df[cols]

# sum over columns 'TF_RNA, TF_PROT, BS_RNA, BS_PROT'
num_nodes = TRRUST_df[['TF_RNA', 'TF_PROT', 'BS_RNA', 'BS_PROT']].nunique().sum()
print(num_nodes)


# write to tsv
TRRUST_df.to_csv('/home/celeroid/Documents/CLS_MSc/Thesis/EcoCancer/MONIKA/Diffusion/data/TRRUST_expanded.tsv', sep='\t', index=False)

# DataFrame for RNA (TF_RNA + BS_RNA)
df_rna = pd.DataFrame({
    'RNA_TF_BS': list(set(TRRUST_df['TF_RNA']) | set(TRRUST_df['BS_RNA']))
})

# DataFrame for Proteins (TF_PROT + BS_PROT)
df_prot = pd.DataFrame({
    'PROT_TF_BS': list(set(TRRUST_df['TF_PROT']) | set(TRRUST_df['BS_PROT']))
})

df_prot.shape


# %%
TRRUST_sample = TRRUST_df.sample(n=10, random_state=1)
# include all rows that have 'ABL1
TRRUST_sample = TRRUST_df[TRRUST_df['TF_PROT'] == 'ABL1']


# # write LINKEDOMICS LINKEDOMICS LINKEDOMICS LINKEDOMICS LINKEDOMICS_df to csv
# TRRUST_df.to_csv('/home/celeroid/Documents/CLS_MSc/Thesis/EcoCancer/MONIKA/Diffusion/TRRUST_adjacency_mat.csv', index=False)
# TRRUST_sample.head()

# Make a 2 column dataframe, first column = set(TF_RNA + BS_RNA), second column = set(TF_PROT + BS_PROT)



# %%
def directed_reactome_adj(edges_df, nodes):
    # Initialize a 100x100 matrix with zeros
    adjacency_matrix = pd.DataFrame(0, index=nodes, columns=nodes)

    # Define sets for undirected and directed interactions
    undirected_annotations = {'complex', 'predicted', 'PPrel: binding/association; complex', 'reaction', 'PPrel: dissociation', 'PPrel: binding/association; complex; input'}
    directed_annotations_gene1_to_gene2 = {'catalyze; input', 'catalyze; reaction', 'PPrel: activation', 'PPrel: activation, indirect effect'}
    directed_annotations_gene2_to_gene1 = {'catalyzed by; complex; input', 'catalyzed by', 'activated by; catalyzed by', 'activated by', 'PPrel: activated by; complex; input'}

    # Iterate over the rows in the edges dataframe
    for _, row in edges_df.iterrows():
        gene1, gene2 = row['name'].split(' (FI) ')
        annotation = row['FI Annotation']

        # Check if both genes are in the nodes list
        if gene1 in nodes and gene2 in nodes:
            # Set undirected edge
            if annotation in undirected_annotations:
                adjacency_matrix.loc[gene1, gene2] = 1
                adjacency_matrix.loc[gene2, gene1] = 1
            
            # Set directed edge from gene1 to gene2
            if annotation in directed_annotations_gene1_to_gene2:
                adjacency_matrix.loc[gene1, gene2] = 1
            
            # Set directed edge from gene2 to gene1
            elif annotation in directed_annotations_gene2_to_gene1:
                adjacency_matrix.loc[gene2, gene1] = 1
    
    return adjacency_matrix

def STRING_adjacency_matrix(nodes_df, edges_df):
    # Mapping Ensembl IDs to 'query term' names
    id_to_query_term = pd.Series(nodes_df['query term'].values, index=nodes_df['name']).to_dict()

    # Create a unique list of 'query terms'
    unique_query_terms = nodes_df['query term'].unique()

    # Initialize an empty adjacency matrix with unique query term labels
    adjacency_matrix = pd.DataFrame(0, index=unique_query_terms, columns=unique_query_terms)

    # Process each edge in the edges file
    for _, row in edges_df.iterrows():
        # Extract Ensembl IDs from the edge and map them to 'query term' names
        gene1_id, gene2_id = row['name'].split(' (pp) ')
        gene1_query_term = id_to_query_term.get(gene1_id)
        gene2_query_term = id_to_query_term.get(gene2_id)

        # Check if both gene names (query terms) are in the list of unique query terms
        if gene1_query_term in unique_query_terms and gene2_query_term in unique_query_terms:
            # Set the undirected edge in the adjacency matrix
            adjacency_matrix.loc[gene1_query_term, gene2_query_term] = 1
            adjacency_matrix.loc[gene2_query_term, gene1_query_term] = 1
        # else: 
            # print(f'!!!{gene1_query_term}{gene2_query_term}')

    return adjacency_matrix


# Loading Edges
edges_all_PROTS = pd.read_csv('/home/celeroid/Documents/CLS_MSc/Thesis/EcoCancer/MONIKA/Diffusion/data/FI_TRRUST_Edges.csv')
STRING_edges_df = pd.read_csv('/home/celeroid/Documents/CLS_MSc/Thesis/EcoCancer/MONIKA/Diffusion/data/RPPA_prior_EDGES85perc.csv')
STRING_nodes_df = pd.read_csv('/home/celeroid/Documents/CLS_MSc/Thesis/EcoCancer/MONIKA/Diffusion/data/RPPA_prior_NODES85perc.csv')


# # Construct the adjacency matrix from STRING
PPI_interactions = STRING_adjacency_matrix(STRING_nodes_df, STRING_edges_df)

# check overlap between STRING_nodes_df and 

# WE CAN ONLY UNCOMMENT THIS ONCE WE LOCATE THE DEA FILES



# # check overlap PPI_interactions and DEA_PROTS_CMS4
# PPI_DEA_PROTS = np.intersect1d(PPI_interactions.columns, DEA_PROTS_CMS4)
# print(f'Number of DEA_PROTS_CMS4 in PPI_interactions: {len(PPI_DEA_PROTS)}\n')

# # check overlap of PPI_interactions and all_PROTS
# PPI_all_PROTS = np.intersect1d(PPI_interactions.columns, all_PROTS)
# print(f'TOTAL # of PROTS in the TRRUST part of scaffold: {len(all_PROTS)}')
# print(f'Intersection of TRRUST PROTS and PPI PROTS: {len(PPI_all_PROTS)}')
# print(f'This means that {len(all_PROTS) - len(PPI_all_PROTS)} PROTS in TRRUST are not in STRING, potentially leading to disconnected components\n')

# # INtersectino between tf_proteins and PPI_DEA_PROTS
# tf_DEA_PROTS = np.intersect1d(tf_proteins, PPI_DEA_PROTS)
# print(f'Number of DEA proteins that are TFs + PPI connected: {len(tf_DEA_PROTS)}')
# print('These could be used for the DEA-centered subgraphs\n')

# # count all 1s in the adjacency matrix
# print(f'Nodes in PPI: {PPI_interactions.shape[0]}')
# print(f'Edges in PPI: {PPI_interactions.sum().sum()}')

PPI_interactions.head()
# write to csv
PPI_interactions.to_csv('/home/celeroid/Documents/CLS_MSc/Thesis/EcoCancer/MONIKA/Diffusion/data/RPPA_prior_adj85perc.csv', index=True)


# %%
def get_gene_role(protein):
    """
    Determine the role of the protein. (Transcription Factor or NOT)
    Args:
    protein (str): The protein name.
    Returns:
    str: The suffix indicating the protein's role.
    """
    # Logic to determine the role
    # For example, using a mapping dictionary or checking specific conditions
    # Return ".p>" for transcription factors, and ".p]" for regulated proteins
    if protein in tf_proteins:
        return ".p>", ".r>"
    elif protein in targeted_PROTS:
        return ".p]", ".r]"
    else:
        return ".p-", ".r-"


def create_scaffold_network(TRRUST_df, PPI_interactions, get_gene_role, directed=False):
    """
    Create an undirected network based on transcription regulatory relationships and protein-protein interactions.

    Args:
    TRRUST_df (DataFrame): DataFrame containing transcription regulatory relationships.
    PPI_interactions (DataFrame): DataFrame containing protein-protein interactions.
    get_gene_role (function): Function to determine the role of genes.

    Returns:
    NetworkX Graph: An undirected graph representing the network.
    """
    if directed:
        # CREATING THE BASIC DOGMA GRAPH
        G = nx.DiGraph()
    else:
        G = nx.Graph()

    # # Add edges for each relationship in TRRUST
    # for _, row in TRRUST_df.iterrows():
    #     if pd.notna(row['TF_RNA']) and pd.notna(row['TF_PROT']):
    #         G.add_edge(row['TF_RNA'] + ".r>", row['TF_PROT'] + ".p>")
    #     if pd.notna(row['TF_PROT']) and pd.notna(row['BS_RNA']):
    #         G.add_edge(row['TF_PROT'] + ".p>", row['BS_RNA'] + '.r]')
    #     if pd.notna(row['BS_RNA']) and pd.notna(row['BS_PROT']):
    #         G.add_edge(row['BS_RNA'] + '.r]', row['BS_PROT'] + ".p]")


    # INTEGRATING the PPI part to get the SCAFFOLD GRAPH
    for gene1 in PPI_interactions.columns:
        for gene2 in PPI_interactions.index:
            # Check if there is an edge from gene1 to gene2
            if PPI_interactions.loc[gene1, gene2] == 1:
                protein1_role, rna1_role = get_gene_role(gene1)
                protein2_role, rna2_role = get_gene_role(gene2)

                # Add edge with appropriate suffixes based on roles
                G.add_edge(gene1 + protein1_role, gene2 + protein2_role)
                # G.add_edge(gene1 + rna1_role, gene1 + protein1_role)
                # G.add_edge(gene2 + rna2_role, gene2 + protein2_role)
    

    return G

# SCAFFOLD_G = create_scaffold_network(TRRUST_df, PPI_interactions, get_gene_role, directed=False)

# Write G to file
# nx.write_graphml(SCAFFOLD_G, 'data/SCAFFOLD_graph.graphml')



# %% Investigating the Subgraph
# load from file
SCAFFOLD_G = nx.read_graphml('data/SCAFFOLD_graph.graphml')

# count nodes and edges
print(f'Number of total nodes: {SCAFFOLD_G.number_of_nodes()}')
print(f'Number of total edges: {SCAFFOLD_G.number_of_edges()}')

# COMPONENT ANALYSIS
components = list(nx.connected_components(SCAFFOLD_G))
num_disconnected_components = len(components)

print('GRAPH COMPONENT ANALYSIS\n-------------------------------')
print(f"Number of graph components: {num_disconnected_components}")

# check length of each component. Check number of edges
for i, component in enumerate(components):
    print(f"Component {i} has {len(component)} nodes")
    print(component)

# set SCAFFOLD_G to the largest component
SCAFFOLD_G = SCAFFOLD_G.subgraph(components[0])

def get_connected_subgraph(G, start_node, num_nodes, mode='bfs'):
    if mode == 'bfs':
        # Perform BFS and get the first 'num_nodes' from the list
        nodes = list(nx.bfs_tree(G, start_node))[:num_nodes]
    else:
        # Perform DFS and get the first 'num_nodes' from the list
        nodes = list(nx.dfs_tree(G, start_node))[:num_nodes]

    # Create a subgraph using these nodes
    subgraph = G.subgraph(nodes)

    return subgraph


# %%
########################################## SUBGRAPHS and SYNTH GRAPHS #####################################################################
print('\n DEA-centered SUBGRAPHS\n-------------------------------')

p = 50  # Define how many nodes you want in the subgraph

def count_common_proteins(subgraph, protein_list):
    # Count how many nodes in the subgraph are in the protein list
    return len([node for node in subgraph.nodes if node in protein_list])

# Initialize variables to track the best subgraph
best_subgraph = None
best_count = 0
best_node = None

for prot in PPI_DEA_PROTS:
    # Generate the subgraph for each node
    top_node = prot + get_gene_role(prot)[0]
    subgraph = get_connected_subgraph(SCAFFOLD_G, top_node, p, mode='bfs')
    
    # Count how many proteins from PPI_DEA_PROTS are in the subgraph
    protein_list = [prot + get_gene_role(prot)[0] for prot in PPI_DEA_PROTS]
    count = count_common_proteins(subgraph, protein_list)
    
    # Update best subgraph if this one has more proteins from the list
    if count > best_count:
        best_subgraph = subgraph
        best_count = count
        best_node = top_node

# Output the best subgraph info
print(f"Best starting node: {best_node}")
print(f"Number of DEA proteins in the best subgraph: {best_count}")

# GEnerating the subgraph that captures the most DEA proteins
subG_undir = get_connected_subgraph(SCAFFOLD_G, best_node, p, mode='bfs')

# Define node colors based on unique node types
node_colors = []
for node in subG_undir:
    if node != top_node:
        if ".p>" in node:
            node_colors.append('firebrick')  # forestgreen Color for 'TF_PROT' nodes
        elif ".p]" in node:
            node_colors.append('rosybrown')     # palegreen Color for 'BS_PROT' nodes
        elif ".p-" in node:
            node_colors.append('salmon') # mediumaquamarine
        elif ".r>" in node:
            node_colors.append('royalblue')    # Color for 'TF_RNA' nodes
        elif ".r]" in node:
            node_colors.append('skyblue') # Color for 'BS_RNA' nodes
    else:
        node_colors.append('yellow')
    # elif ".r-" in node:
    #     node_colors.append('mediumturquoise') # Color for 'RNA' nodes


# # count number of nodes with ".r" suffix
# wiring_rna = len([node for node in subG_undir.nodes() if ".r-" in node])
wiring_prots = len([node for node in subG_undir.nodes() if ".p-" in node])
tf_rna = len([node for node in subG_undir.nodes() if ".r>" in node])
tf_prots = len([node for node in subG_undir.nodes() if ".p>" in node])
bs_rna = len([node for node in subG_undir.nodes() if ".r]" in node])
bs_prots = len([node for node in subG_undir.nodes() if ".p]" in node])

print(f'Sum of all node types: {wiring_prots + tf_rna + tf_prots + bs_rna + bs_prots}')
print(f'wiring_prots: {wiring_prots}, tf_rna: {tf_rna}, tf_prots: {tf_prots}, bs_rna: {bs_rna}, bs_prots: {bs_prots}')
# plot distribution
plt.bar(['wiring_prots', 'tf_rna', 'tf_prots', 'bs_rna', 'bs_prots'], [wiring_prots, tf_rna, tf_prots, bs_rna, bs_prots])
plt.xlabel('Node Type')
plt.ylabel('Frequency')
plt.title(fr'Node Type Distribution for {len(subG_undir)} nodes')
plt.xticks(rotation=45)
plt.show()

print(f'Total number of proteins in subG: {tf_prots + bs_prots + wiring_prots}')
print(f'Total number of RNAs in subG: {tf_rna + bs_rna}')
print(f'total number of edges in subG: {subG_undir.number_of_edges()}')


# Draw the undirected subgraph
plt.figure(figsize=(10, 10), dpi=300)
nx.draw_networkx(subG_undir, pos=nx.spring_layout(subG_undir, weight=1),
                 node_size=250,
                 with_labels=True,
                 font_size=5,
                 font_color='black',
                 edge_color='grey',
                 node_color=node_colors,
                 alpha=0.75)

# Show the plot
plt.show()



# %%
################################################### EXPORTING FOR PIGLASSO
# Get pandas dataframe of the subgraph
subG_undir_df = nx.to_pandas_edgelist(subG_undir)
subG_undir_df.head()

# get adjacency matrix with node names
subG_undir_adj = nx.to_pandas_adjacency(subG_undir)
subG_undir_adj.head()

# remove suffixes from node names
subG_undir_adj.columns = [col.split('.')[0] for col in subG_undir_adj.columns]
subG_undir_adj.index = [index.split('.')[0] for index in subG_undir_adj.index]

#write to csv
subG_undir_adj.to_csv(f'data/SUBGRAPH_ADJACENCY_PROT_{p}.csv', index=True)

cms_protein_file = pd.read_csv('../data/Synapse/TCGA/Proteomics_CMS_groups/TCGACRC_proteomics_ALL_labelled.csv', index_col=0)
cms_rna_file = pd.read_csv('../data/Synapse/TCGA/TCGACRC_expression.tsv', sep='\t', index_col=0)

cms_protein_file = cms_protein_file.transpose()
cms_rna_file = cms_rna_file.transpose()


# only keep columns that are in subG_undir_adj
cms_protein_file = cms_protein_file[subG_undir_adj.columns]
# filter the columns of cms_rna_file
common_protein_rna = subG_undir_adj.columns.intersection(cms_rna_file.columns)
cms_rna_file = cms_rna_file[common_protein_rna]

# cms_protein_file.head()
# cms_rna_file.head()


# write to csv
cms_protein_file.to_csv(f'data/TCGACRC_proteomics_SUBGRAPH_SELECT_{p}.csv', index=True)
cms_rna_file.to_csv(f'data/TCGACRC_transcriptomics_SUBGRAPH_SELECT_{p}.csv', index=True)

# %%

# prot_file = pd.read_csv('../data/Synapse/TCGA/TCGACRC_proteomics.csv', index_col=0)

# # sum over values of "TCGA-A6-3807-01A-22" column
# prot_file['TCGA-A6-3807-01A-22'] = prot_file['TCGA-A6-3807-01A-22'].astype(float)
# sumcheck = prot_file['TCGA-A6-3807-01A-22'].sum()
# print(f'Sum of values in TCGA-A6-3807-01A-22 column: {sumcheck}')
# # RANDOM GRAPH
# random_g = nx.erdos_renyi_graph(p, 0.1, seed=6, directed=False)

# # SCALE FREE GRAPH
# if p <= 100:
#     m = random.choice([1,2,2])
# elif 100 < p <= 300:
#     m = random.choice([3,5,6])
# elif 300 < p <= 500:
#     m = random.choice([5,8,10])
# elif 500 < p <= 1000:
#     m = random.choice([10,15,20])
# else:
#     m = 20

# scale_free_g = nx.barabasi_albert_graph(p, m, seed=42)

# def graph_analysis(network):
#     # get degree distribution
#     degrees = [val for (node, val) in network.degree()]
#     plt.hist(degrees, bins=20)
#     plt.xlabel('Degree')
#     plt.ylabel('Frequency')
#     plt.title(fr'Degree Distribution for {len(degrees)} nodes')
#     plt.show()

#     # plot on a log-log scale
#     plt.scatter(np.log10(range(1, len(degrees) + 1)), np.log10(sorted(degrees, reverse=True)))
#     plt.xlabel('log10(Rank)')
#     plt.ylabel('log10(Degree)')
#     plt.title(fr'Log-Log Degree Distribution for {len(degrees)} nodes')
#     plt.show()

# # graph_analysis(subG_undir)
# %%
