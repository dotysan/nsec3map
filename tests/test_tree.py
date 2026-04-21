"""Tests for n3map.tree — BSTree and RBTree."""

import pytest

from n3map.tree.bstree import BSTree
from n3map.tree.rbtree import RBTree, RBTreeNode


def _insert(tree, key, value):
    """Helper: create a node and insert it."""
    node = RBTreeNode(k=key, v=value, nil=tree.nil)
    return tree.insert_node(node)


class TestBSTree:
    def test_empty_tree_find(self):
        tree = BSTree()
        assert tree.find(1) is None

    def test_empty_tree_contains(self):
        tree = BSTree()
        assert tree.contains(1) is False


class TestRBTree:
    def test_insert_and_find(self):
        tree = RBTree()
        _insert(tree, 5, "five")
        _insert(tree, 3, "three")
        _insert(tree, 7, "seven")
        assert tree.find(5).value == "five"
        assert tree.find(3).value == "three"
        assert tree.find(7).value == "seven"

    def test_find_missing(self):
        tree = RBTree()
        _insert(tree, 1, "one")
        assert tree.find(99) is None

    def test_minimum_maximum(self):
        tree = RBTree()
        for i in [5, 3, 7, 1, 9]:
            _insert(tree, i, str(i))
        assert tree.minimum().key == 1
        assert tree.maximum().key == 9

    def test_contains(self):
        tree = RBTree()
        _insert(tree, 42, "answer")
        assert tree.contains(42) is True
        assert tree.contains(0) is False

    def test_successor(self):
        tree = RBTree()
        for i in [1, 2, 3, 4, 5]:
            _insert(tree, i, str(i))
        node = tree.find(3)
        succ = tree.successor(node)
        assert succ.key == 4

    def test_predecessor(self):
        tree = RBTree()
        for i in [1, 2, 3, 4, 5]:
            _insert(tree, i, str(i))
        node = tree.find(3)
        pred = tree.predecessor(node)
        assert pred.key == 2

    def test_delete(self):
        tree = RBTree()
        _insert(tree, 1, "a")
        _insert(tree, 2, "b")
        _insert(tree, 3, "c")
        node = tree.find(2)
        tree.delete(node)
        assert tree.find(2) is None
        assert tree.find(1) is not None
        assert tree.find(3) is not None

    def test_inorder(self):
        tree = RBTree()
        for i in [5, 2, 8, 1, 3]:
            _insert(tree, i, str(i))
        keys = []
        tree.inorder(lambda x: keys.append(x.key))
        assert keys == [1, 2, 3, 5, 8]

    def test_many_insertions_balanced(self):
        tree = RBTree()
        for i in range(100):
            _insert(tree, i, str(i))
        # All inserted keys should be findable
        for i in range(100):
            assert tree.contains(i)
        assert tree.minimum().key == 0
        assert tree.maximum().key == 99

    def test_size(self):
        tree = RBTree()
        for i in range(10):
            _insert(tree, i, str(i))
        assert tree.size() == 10
