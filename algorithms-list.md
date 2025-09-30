Here is The base list of algorithms used to seed the database.

---

## Category - Search & Optimization
- **A\* Search Algorithm** - Pathfinding and graph traversal using heuristics.
- **Beam Search** - A heuristic search that expands the most promising nodes.
- **Best-first Search** - Uses an evaluation function to decide which node to expand.
- **Binary Search** - Efficiently finds a target in a sorted array.
- **Breadth-First Search (BFS)** - Explores all nodes at the present depth before moving deeper.
- **Depth-First Search (DFS)** - Explores as far as possible along a branch before backtracking.
- **Dijkstra’s Algorithm** - Finds the shortest path between nodes in a graph.
- **Floyd–Warshall Algorithm** - Finds shortest paths in a weighted graph.
- **Gradient Descent** - Iterative optimization algorithm for minimizing a function.
- **Hill Climbing** - A local search that moves in the direction of increasing value.
- **Simulated Annealing** - Probabilistic technique for approximating the global optimum.
- **Tabu Search** - Uses memory structures to avoid revisiting solutions.

## Category - Sorting & Ordering
- **Bubble Sort** - Repeatedly swaps adjacent elements if they are in the wrong order.
- **Heap Sort** - Comparison-based sorting using a binary heap.
- **Insertion Sort** - Builds the sorted array one item at a time.
- **Merge Sort** - Divides the array into halves, sorts them, and merges.
- **Quick Sort** - Divide-and-conquer algorithm with a pivot element.
- **Radix Sort** - Sorts numbers by processing individual digits.
- **Selection Sort** - Repeatedly selects the smallest element from the unsorted portion.
- **Timsort** - Hybrid sorting derived from merge sort and insertion sort.

## Category - Machine Learning
- **Apriori Algorithm** - Finds frequent itemsets for association rule learning.
- **Backpropagation** - Trains neural networks by propagating errors backward.
- **Decision Tree** - Uses a tree-like model of decisions for classification/regression.
- **Expectation-Maximization (EM) Algorithm** - Finds maximum likelihood estimates in probabilistic models.
- **Gradient Boosting** - Builds models sequentially, each correcting its predecessor.
- **K-Means Clustering** - Partitions data into k clusters based on similarity.
- **K-Nearest Neighbors (KNN)** - Classifies based on the majority class of k nearest neighbors.
- **Naive Bayes Classifier** - Applies Bayes' theorem with strong independence assumptions.
- **Principal Component Analysis (PCA)** - Reduces dimensionality while preserving variance.
- **Random Forest** - Ensemble learning method using multiple decision trees.
- **Support Vector Machines (SVM)** - Finds the optimal hyperplane for classification.
- **Viterbi Algorithm** - Finds the most likely sequence of hidden states in a Markov model.

## Category - Cryptography & Hashing
- **Advanced Encryption Standard (AES)** - Symmetric encryption algorithm.
- **Diffie–Hellman Key Exchange** - Establishes a shared secret over an insecure channel.
- **MD5** - Widely used hash function (now considered cryptographically broken).
- **RSA Algorithm** - Asymmetric cryptography for secure data transmission.
- **SHA-2 / SHA-3** - Family of cryptographic hash functions.
- **Bloom Filter** - Probabilistic data structure for testing set membership.

## Category - Numerical & Mathematical
- **Euclidean Algorithm** - Computes the greatest common divisor (GCD).
- **Fast Fourier Transform (FFT)** - Efficiently computes the Discrete Fourier Transform.
- **Gaussian Elimination** - Solves systems of linear equations.
- **Newton's Method** - Finds roots of a real-valued function.
- **Simplex Algorithm** - Solves linear programming problems.

## Category - Graph & Network Algorithms
- **Bellman–Ford Algorithm** - Computes shortest paths with negative weights.
- **Kruskal’s Algorithm** - Finds a minimum spanning tree for a graph.
- **PageRank Algorithm** - Ranks web pages based on link structure.
- **Prim’s Algorithm** - Finds a minimum spanning tree in a weighted graph.
- **Tarjan’s Algorithm** - Finds strongly connected components in a graph.
- **Topological Sort** - Orders vertices in a directed acyclic graph.

## Category - Bioinformatics & Sequence Analysis
- **Needleman–Wunsch Algorithm** - Performs global sequence alignment.
- **Smith–Waterman Algorithm** - Performs local sequence alignment.

## Category - Computer Graphics & Vision
- **Canny Edge Detector** - Detects edges in images.
- **Marching Cubes** - Extracts a polygonal mesh from a 3D scalar field.
- **Ray Tracing** - Renders images by simulating the path of light.
- **Seam Carving** - Content-aware image resizing.

## Category - Compression & Encoding
- **Huffman Coding** - Lossless data compression using variable-length codes.
- **Lempel–Ziv–Welch (LZW)** - Universal lossless data compression.
- **Run-Length Encoding (RLE)** - Compresses sequences of the same value.

## Category - Distributed & Concurrent Systems
- **Banker’s Algorithm** - Avoids deadlock in resource allocation.
- **Lamport’s Bakery Algorithm** - Ensures mutual exclusion in concurrent systems.
- **Paxos Algorithm** - Reaches consensus in a distributed system.

## Category - Primality & Number Theory
- **Miller–Rabin Primality Test** - Probabilistic test for determining if a number is prime.
- **Sieve of Eratosthenes** - Finds all primes up to a specified integer.

# Additional Machine Learning Algorithms by Category

## Category -  Supervised Learning

### Classification
- **Logistic Regression** - Statistical model for binary classification using logistic function
- **Linear Discriminant Analysis (LDA)** - Finds linear combination of features that separates classes
- **Quadratic Discriminant Analysis (QDA)** - Nonlinear version of LDA with quadratic decision boundaries
- **Passive-Aggressive Algorithms** - Online learning algorithms for classification
- **Label Propagation** - Semi-supervised classification using graph-based label spreading
- **Gaussian Process Classification** - Non-parametric Bayesian approach to classification

### Regression
- **Lasso Regression** - Linear regression with L1 regularization for feature selection
- **Elastic Net** - Combines L1 and L2 regularization (Lasso + Ridge)
- **Bayesian Linear Regression** - Probabilistic approach to linear regression
- **Gaussian Process Regression** - Non-parametric Bayesian regression
- **Quantile Regression** - Estimates conditional quantiles rather than means
- **Theil-Sen Estimator** - Robust regression method resistant to outliers

## Category -  Clustering
- **Affinity Propagation** - Clustering by passing messages between data points
- **Spectral Clustering** - Uses eigenvalues of similarity matrix for clustering
- **Mean Shift** - Non-parametric clustering based on density estimation
- **BIRCH** - Balanced Iterative Reducing and Clustering using Hierarchies
- **CLARA** - Clustering Large Applications (scalable version of PAM)
- **CLARANS** - Clustering Large Applications based on RANdomized Search
- **Fuzzy C-means** - Soft clustering where points can belong to multiple clusters
- **Gaussian Mixture Models (GMM)** - Probabilistic model-based clustering
- **HDBSCAN** - Hierarchical density-based clustering

## Category -  Dimensionality Reduction
- **t-SNE (t-Distributed Stochastic Neighbor Embedding)** - Nonlinear dimensionality reduction for visualization
- **UMAP** - Uniform Manifold Approximation and Projection
- **Isomap** - Nonlinear technique using geodesic distances
- **Locally Linear Embedding (LLE)** - Nonlinear dimensionality preserving local relationships
- **Multidimensional Scaling (MDS)** - Preserves pairwise distances between points
- **Factor Analysis** - Models observed variables with latent factors
- **Independent Component Analysis (ICA)** - Finds statistically independent components
- **Linear Discriminant Analysis (LDA)** - Supervised dimensionality reduction
- **Autoencoders** - Neural network-based dimensionality reduction

## Category -  Structured Prediction
- **Structured Perceptron** - Extension of perceptron to structured outputs
- **Max-Margin Markov Networks (M³N)** - Maximum margin approach for structured prediction
- **Learning to Search** - Frameworks like SEARN and DAgger for structured prediction
- **Structured Prediction Energy Networks (SPENs)** - Energy-based models for structured outputs

## Category - Anomaly Detection
- **Isolation Forest** - Tree-based method that isolates anomalies
- **Local Outlier Factor (LOF)** - Measures local density deviation
- **One-Class SVM** - Learns a decision boundary around normal data
- **Autoencoder Reconstruction Error** - Uses reconstruction loss to detect anomalies
- **Elliptic Envelope** - Fits an ellipse around normal data points
- **Histogram-Based Outlier Detection (HBOS)** - Univariate method combining histograms

## Category -  Neural Networks
- **Transformer Architecture** - Self-attention based architecture (BERT, GPT, etc.)
- **U-Net** - Convolutional network for image segmentation
- **ResNet** - Residual networks with skip connections
- **Inception Network** - Multiple filter sizes in parallel
- **DenseNet** - Densely connected convolutional networks
- **Capsule Networks** - Groups neurons into capsules that represent entities
- **Spiking Neural Networks** - Bio-inspired networks with temporal dynamics
- **Liquid State Machines** - Reservoir computing approach
- **Echo State Networks** - Recurrent networks with fixed hidden weights
- **Neural Ordinary Differential Equations** - Continuous-depth models
- **Graph Neural Networks (GNN)** - Neural networks for graph-structured data
- **Graph Convolutional Networks (GCN)** - Convolutional operations on graphs
- **Attention Mechanisms** - Self-attention, cross-attention, etc.

## Category -  Reinforcement Learning
- **Deep Q-Network (DQN)** - Q-learning with deep neural networks
- **Double DQN** - Addresses overestimation bias in DQN
- **Dueling DQN** - Separates value and advantage streams
- **Policy Gradient Methods** - REINFORCE, direct policy optimization
- **Actor-Critic Methods** - Combines policy and value function learning
- **Proximal Policy Optimization (PPO)** - Stable policy gradient method
- **Trust Region Policy Optimization (TRPO)** - Constrained policy updates
- **Soft Actor-Critic (SAC)** - Maximum entropy reinforcement learning
- **Twin Delayed DDPG (TD3)** - Addresses overestimation in continuous control
- **Monte Carlo Tree Search (MCTS)** - Heuristic search for decision processes
- **Hierarchical Reinforcement Learning** - Learning at multiple temporal abstractions
- **Inverse Reinforcement Learning** - Inferring rewards from expert demonstrations
- **Multi-Agent Reinforcement Learning** - Algorithms for multiple interacting agents

## Category -  Ensemble Methods
- **XGBoost** - Optimized gradient boosting implementation
- **LightGBM** - Gradient boosting framework using tree-based learning
- **CatBoost** - Gradient boosting for categorical features
- **Stacking** - Combines multiple models via meta-learner
- **Voting Classifiers** - Hard and soft voting ensembles

## Category -  Time Series
- **ARIMA** - AutoRegressive Integrated Moving Average
- **Exponential Smoothing** - Holt-Winters methods
- **Prophet** - Decomposable time series model
- **LSTM for Time Series** - Recurrent networks for sequential data
- **Temporal Convolutional Networks** - CNN-based time series modeling