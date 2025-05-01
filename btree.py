import bisect
from typing import Any, List, Optional, Tuple, Union, Dict, Generic, TypeVar, cast, NewType
from py_btrees.disk import DISK, Address
from py_btrees.btree_node import BTreeNode, KT, VT, get_node

"""
----------------------- Starter code for your B-Tree -----------------------

Helpful Tips (You will need these):
1. Your tree should be composed of BTreeNode objects, where each node has:
    - the disk block address of its parent node
    - the disk block addresses of its children nodes (if non-leaf)
    - the data items inside (if leaf)
    - a flag indicating whether it is a leaf

------------- THE ONLY DATA STORED IN THE `BTree` OBJECT SHOULD BE THE `M` & `L` VALUES AND THE ADDRESS OF THE ROOT NODE -------------
-------------              THIS IS BECAUSE THE POINT IS TO STORE THE ENTIRE TREE ON DISK AT ALL TIMES                    -------------

2. Create helper methods:
    - look at btree_node.get_node this be useful getting root node.
    - get a node's parent with DISK.read(parent_address), done already see BTreeNode.get_parent
    - get a node's children with DISK.read(child_address), done already see BTreeNode.get_child
    - write a node back to disk with DISK.write(self), done already see BTreeNode.write_back
    - check the health of your tree (makes debugging a piece of cake)
        - go through the entire tree recursively and check that children point to their parents, etc.
        - now call this method after every insertion in your testing and you will find out where things are going wrong
3. Don't fall for these common bugs:
    - Forgetting to update a node's parent address when its parent splits
        - Remember that when a node splits, some of its children no longer have the same parent
    - Forgetting that the leaf and the root are edge cases
    - FORGETTING TO WRITE BACK TO THE DISK AFTER MODIFYING / CREATING A NODE
    - Forgetting to test odd / even M values
    - Forgetting to update the KEYS of a node who just gained a child
    - Forgetting to redistribute keys or children of a node who just split
    - Nesting nodes inside of each other instead of using disk addresses to reference them
        
class BTree:
    def __init__(self, M: int, L: int):
        """
        Initialize a new BTree.
    
        M: The maximum number of keys allowed in an internal (non-leaf) node before it must be split.
        L: The maximum number of keys allowed in a leaf node before it must be split.
            Stores only three pieces of data in memory:
           - M
           - L
           - root_addr (the disk address of the root node)]
        """
        self.root_addr: Address = DISK.new() # Remember, this is the ADDRESS of the root node
        # DO NOT RENAME THE ROOT MEMBER -- LEAVE IT AS self.root_addr
        DISK.write(self.root_addr, BTreeNode(self.root_addr, None, None, True))
        self.M = M # M will fall in the range 2 to 99999
        self.L = L # L will fall in the range 1 to 99999



    def insert(self, key: KT, value: VT) -> None:
        """
        Insert the key-value pair into your tree.
        It will probably be useful to have an internal
        _find_node() method that searches for the node
        that should be our parent (or finds the leaf
        if the key is already present).

        Overwrite old values if the key exists in the BTree.

        Make sure to write back all changes to the disk!
        """
        # Start at root and go down to the appropriate leaf
        node=get_node(self.root_addr)
        path=[]

        while not node.is_leaf:
            idx=node.find_idx(key)
        # Track path for potential upward splits
            path.append((node,key))
            node=node.get_child(idx)

        # Insert key-value into the leaf node
        node.insert_data(key,value)
        node.write_back()

        # If length exceeds, initiate split
        if len(node.keys)>self.L:
            self.split_leaf(node,path)

    def split_leaf(self, node: BTreeNode, path: List[Tuple[BTreeNode, int]]):
        """
                splits a leaf node that exceeds the limit L.

                - Splits the node into two halves.
                - The first key of the new right node is promoted to the parent.
                - If the node is the root, a new root is created.

        """
        # Find midpoint for split
        mid = len(node.keys) // 2
        new_node_addr = DISK.new()
        new_node = BTreeNode(new_node_addr, None, None, True)

        # Divide keys and data into two halves
        new_node.keys = node.keys[mid:]
        new_node.data = node.data[mid:]
        node.keys = node.keys[:mid]
        node.data = node.data[:mid]

        new_node.write_back()
        node.write_back()

        mid_key = new_node.keys[0] # Promote first key of new node

        if not path:
            # Splitting root — create new root
            new_root_addr = DISK.new()
            new_root = BTreeNode(new_root_addr, None, None, False)
            new_root.keys = [mid_key]
            new_root.children_addrs = [node.my_addr, new_node_addr]
            node.parent_addr = new_root_addr
            new_node.parent_addr = new_root_addr
            node.index_in_parent = 0
            new_node.index_in_parent = 1
            new_root.write_back()
            node.write_back()
            new_node.write_back()
            self.root_addr = new_root_addr
            return
        # Update parent node with promoted key
        parent, _ = path.pop()
        sorted_idx = parent.find_idx(mid_key)
        parent.keys.insert(sorted_idx, mid_key)
        parent.children_addrs.insert(sorted_idx + 1, new_node_addr)

        node.parent_addr = parent.my_addr
        new_node.parent_addr = parent.my_addr
        node.index_in_parent = sorted_idx
        new_node.index_in_parent = sorted_idx + 1

        parent.write_back()
        node.write_back()
        new_node.write_back()

        # If parent now exceeds max keys, split it
        if len(parent.keys) >= self.M:
            self.split_internal(parent, path)


    def split_internal(self, node: BTreeNode, path: List[Tuple[BTreeNode, int]]):
        """
        Splits an internal (non-leaf) node when it exceeds M.

        - Promotes the middle key to the parent.
        - Keys and children are split around the middle key into two internal nodes.
        - Updates the children's parent and index_in_parent references accordingly.
        - If the node is the root, a new root is created.
        """
        #maintains A non-leaf node with k children contains k - 1 keys
        # Identify middle key for promotion
        mid = len(node.keys) // 2
        mid_key = node.keys[mid]

        # Create new sibling node
        new_node_addr = DISK.new()
        new_node = BTreeNode(new_node_addr, None, None, False)

        # Split keys and children between original and new node
        new_node.keys = node.keys[mid + 1:]
        new_node.children_addrs = node.children_addrs[mid + 1:]

        # Update children's parent and index_in_parent
        for i, child_addr in enumerate(new_node.children_addrs):
            child = get_node(child_addr)
            child.parent_addr = new_node_addr
            child.index_in_parent = i
            child.write_back()

        node.keys = node.keys[:mid]
        node.children_addrs = node.children_addrs[:mid + 1]

        node.write_back()
        new_node.write_back()

        if not path:
            # Splitting root — create a new root node
            new_root_addr = DISK.new()
            new_root = BTreeNode(new_root_addr, None, None, False)
            new_root.keys = [mid_key]
            new_root.children_addrs = [node.my_addr, new_node_addr]
            node.parent_addr = new_root_addr
            node.index_in_parent = 0
            new_node.parent_addr = new_root_addr
            new_node.index_in_parent = 1
            new_root.write_back()
            node.write_back()
            new_node.write_back()
            self.root_addr = new_root_addr
            return

        # Insert promoted key into parent
        parent, idx = path.pop()
        sorted_idx = parent.find_idx(mid_key)
        parent.keys.insert(sorted_idx, mid_key)
        parent.children_addrs.insert(sorted_idx + 1, new_node_addr)

        node.parent_addr = parent.my_addr
        new_node.parent_addr = parent.my_addr
        node.index_in_parent = sorted_idx
        new_node.index_in_parent = sorted_idx + 1

        parent.write_back()
        node.write_back()
        new_node.write_back()

        # Recursively split if parent overflows
        if len(parent.keys) >= self.M:
            self.split_internal(parent, path)


    def find(self, key: KT) -> Optional[VT]:
        """
        Find a key and return the value associated with it.
        If it is not in the BTree, return None.

        This should be implemented with a logarithmic search
        in the node.keys array, not a linear search. Look at the
        BTreeNode.find_idx() method for an example of using
        the builtin bisect library to search for a number in 
        a sorted array in logarithmic time.

        Traversal logic:
        - Start from the root node, which is loaded using its disk address via get_node(self.root_addr).
        - At each internal node, use find_idx to determine the correct child pointer to follow.
        - Recursively descend until reaching a leaf node.
        - Then use find_data, which uses the index to check if the key exists and returns the value.
        """
        node = get_node(self.root_addr)
        while not node.is_leaf:
            idx = node.find_idx(key)
            if idx < len(node.keys) and node.keys[idx] == key:
                idx += 1
            node = node.get_child(idx)
        return node.find_data(key)


