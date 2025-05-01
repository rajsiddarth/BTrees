# Implementing BTrees Data Structure
B-Trees are an important data structure that are used to store large (and at times distributed) dictionaries, such as filesystems and databases. Thus, B-Trees support the three Dictionary operations:
1. find(key) -> value: Retrieve the value associated with the given key, if one exists.
2. insert(key, value): Insert the given key into the dictionary and associate with it the given value.
3. delete(key): Delete the given key and its associated value.

To minimize disk accesses, B-Trees are short and wide m-ary trees, where m is an integer > 2 that is chosen to fit as many keys and pointers into a node as possible, where the size of each node is defined by the size of a disk block. Similarly, the constant l is chosen to pack as many data items as possible into a disk block.

## Definition of a B-Tree:
- Each node has at most m children
- Each non-leaf and non-root node has at least [m/2] children
- A non-leaf node with k children contains k− 1 comparable keys
- The root, if it isn’t a leaf, has at least 2 children
- Each leaf node holds between [l/2] and l data items
- If the leaf is the root, it can have a minimum of zero data items
-  All leaves reside at the same level

btree.py gives working implementation of a B-Tree dictionary that supports the find and insert methods.

Disk interface is abstracted through the disk.py module.
