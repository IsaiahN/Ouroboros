Here is The base list of data structs available

---
# Data Structures Categorized

## 📊 Primitive Data Types
- **Boolean** – Represents `true` or `false` values
- **Character** – Represents a single character/symbol
- **Integer** – Represents whole numbers
- **Floating-point** – Represents real numbers with decimal precision
- **Fixed-point** – Represents rational numbers with fixed precision
- **Reference** – Value that refers to another value (pointer/handle)
- **Symbol** – Unique identifier
- **Complex** – Represents complex numbers
- **Enumerated type** – Set of named constants

## 🧱 Composite Data Types
- **Array** – Contiguous sequence of elements of the same type
- **Record/Struct** – Collection of named fields
- **Tuple** – Ordered collection of elements (unnamed fields)
- **String** – Sequence of characters representing text
- **Union** – Datum that can be one of several types
- **Tagged Union** – Union with metadata indicating the current type

## 📦 Abstract Data Types
### Containers
- **List** – Ordered collection allowing duplicates
- **Stack** – LIFO (Last-In-First-Out) structure
- **Queue** – FIFO (First-In-First-Out) structure
- **Priority Queue** – Queue where elements have priority
- **Double-ended Queue** – Queue allowing insertion/removal at both ends
- **Set** – Collection of unique elements
- **Multiset (Bag)** – Set allowing duplicate elements
- **Map/Associative Array** – Key-value pairs
- **Multimap** – Map allowing multiple values per key

## 📈 Linear Data Structures
### Arrays
- **Dynamic Array** – Resizable array
- **Bit Array** – Compact array of bits
- **Circular Buffer** – Fixed-size buffer that wraps around
- **Sparse Matrix** – Efficient representation for matrices with many zeros
- **Parallel Array** – Multiple arrays storing different attributes of objects

### Lists
- **Singly Linked List** – Linear collection of nodes pointing to next
- **Doubly Linked List** – Nodes point to both next and previous
- **Skip List** – Multi-level linked list for fast search
- **Unrolled Linked List** – Each node contains multiple elements
- **XOR Linked List** – Memory-efficient doubly linked list using XOR

## 🌳 Tree Structures
### Binary Trees
- **Binary Search Tree** – Ordered binary tree for efficient search
- **AVL Tree** – Self-balancing binary search tree
- **Red-Black Tree** – Self-balancing tree with color properties
- **Splay Tree** – Self-adjusting binary search tree
- **Treap** – Combination of binary search tree and heap
- **B-tree** – Self-balancing tree for disk storage systems
- **B+ Tree** – B-tree variant optimized for databases

### Heaps
- **Binary Heap** – Complete binary tree satisfying heap property
- **Fibonacci Heap** – Collection of trees with improved amortized performance
- **Binomial Heap** – Collection of binomial trees
- **Pairing Heap** – Simple, efficient heap implementation

### Specialized Trees
- **Trie** – Tree for storing associative arrays with string keys
- **Suffix Tree** – Tree containing all suffixes of a string
- **Segment Tree** – Tree for storing intervals or segments
- **KD-tree** – Space-partitioning tree for multidimensional data
- **Quadtree** – Tree structure for 2D spatial partitioning
- **Octree** – Tree structure for 3D spatial partitioning
- **Merkle Tree** – Tree for verifying data integrity (blockchain)

## 🔄 Hash-based Structures
- **Hash Table** – Array-based structure using hash function
- **Bloom Filter** – Probabilistic data structure for set membership
- **Hash Map** – Hash table implementation of map ADT
- **Distributed Hash Table** – Decentralized hash table
- **Hash Tree** – Tree where leaves are hash values of data blocks

## 🕸️ Graph Structures
- **Graph** – Collection of nodes and edges
- **Adjacency List** – Graph representation using lists
- **Adjacency Matrix** – Graph representation using matrix
- **Directed Graph** – Graph with directed edges
- **Directed Acyclic Graph (DAG)** – Directed graph with no cycles
- **Hypergraph** – Graph where edges connect multiple vertices

## 🎯 Specialized Structures
- **Disjoint-set** – Tracks elements partitioned into disjoint subsets
- **Bloom Filter** – Space-efficient probabilistic membership test
- **Count-Min Sketch** – Probabilistic data structure for frequency estimation
- **Circuit Graphs** – AND-inverter graphs, Binary Decision Diagrams
- **Scene Graph** – Hierarchical structure for graphical scenes
- **Parse Tree** – Tree representing grammatical structure
- **Expression Tree** – Tree representing mathematical expressions

---

This categorized list removes duplicates and organizes data structures by their primary use cases and characteristics, making it easier to understand their relationships and appropriate applications.