from __future__ import annotations


from typing import Generic, Iterator, Sequence, TypeVar
import warnings


T = TypeVar("T")


def _connect_nodes(prev: Node | None, next: Node | None) -> None:
    """Connect two nodes in a graph."""
    if prev is not None:
        prev._next = next
    if next is not None:
        next._prev = prev


def _connect_node_sequence(nodes: Sequence[Node]) -> None:
    """Connect a sequence of nodes in a graph."""
    if not nodes:
        return
    for i in range(len(nodes) - 1):
        _connect_nodes(nodes[i], nodes[i + 1])


class LinkedElement(Generic[T]):
    """A linked element in a doubly linked list."""

    def __init__(self, value: T, owning_list: DoublyLinkedList) -> None:
        self.owning_list = owning_list
        self._value = value
        self._prev = None
        self._next = None
        self._erased = False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._value})"

    def __str__(self) -> str:
        return repr(self)

    @property
    def value(self) -> T:
        return self._value

    @property
    def prev(self) -> T | None:
        return self._prev

    @property
    def next(self) -> T | None:
        return self._next

    def erase(self) -> None:
        """Remove the element from the list."""
        if self._erased:
            warnings.warn(f"Node {self} is already erased", stacklevel=1)
            return
        self._erased = True

    def is_erased(self) -> bool:
        """Return whether the element is erased."""
        return self._erased


class DoublyLinkedList(Sequence[T]):
    """A doubly linked list of nodes.

    This list supports adding and removing nodes from the list during iteration.
    """

    def __init__(self) -> None:
        """Initialize the list.

        Args:
            graph: The :class:`Graph` that the list belongs to.
        """
        self._head: LinkedElement | None = None
        self._tail: LinkedElement | None = None
        self._length = 0

    def __iter__(self) -> Iterator[T]:
        """Iterate over the nodes in the list.

        - If new nodes are inserted after the current node, we will
            iterate over them as well.
        - If new nodes are inserted before the current node, they will
            not be iterated over in this iteration.
        - If the current node is lifted and inserted in a different location,
            iteration will start from the "next" node at the new location.
        """
        elem = self._head
        while elem is not None:
            if not elem.is_erased():
                yield elem.value
            elem = elem.next
        # TODO: Find the right time to call _remove_erased_nodes

    def __len__(self) -> int:
        return self._length

    def __getitem__(self, index: int) -> T:
        if index >= len(self):
            # TODO: check negative index too
            raise IndexError("Index out of range")
        if index < 0:
            # Look up from the end of the list
            raise NotImplementedError("Implement iteration from the back")

        iterator = iter(self)
        item = next(iterator)
        for _ in range(index):
            item = next(iterator)
        return item

    # def _remove_erased_nodes(self) -> None:
    #     node = self._head
    #     while node is not None:
    #         if node._erased:
    #             # prev <-> node <-> next
    #             # prev <-> next
    #             if node._prev is not None:
    #                 node._prev._next = node._next
    #             if node._next is not None:
    #                 node._next._prev = node._prev
    #             if self._head is node:
    #                 self._head = node._next
    #             if self._tail is node:
    #                 self._tail = node._prev
    #             node._graph = None
    #         node = node._next

    def append(self, node: Node) -> None:
        """Append a node to the list."""
        if len(self) == 0:
            assert self._head is None, "Bug: The head should be None when the length is 0"
            assert self._tail is None, "Bug: The tail should be None when the head is None"
            self._head = node
            self._tail = node
            node._graph = self._graph
            node._erased = False
            self._length += 1
        else:
            assert self._head is not None
            assert self._tail is not None
            # Append the node to the end of the list
            self.insert_after(self._tail, (node,))

    def extend(self, nodes: Sequence[Node]) -> None:
        if len(nodes) == 0:
            return
        if len(self) == 0:
            # Insert the first node first
            assert self._head is None, "Bug: The head should be None when the length is 0"
            assert self._tail is None, "Bug: The tail should be None when the head is None"
            first_node = nodes[0]
            first_node._erased = False
            first_node._graph = self._graph
            first_node._prev = None
            first_node._next = None
            self._head = first_node
            self._tail = first_node
            self._length += 1
        # Insert the rest of the nodes
        assert self._tail is not None
        self.insert_after(self._tail, nodes[1:])

    def erase(self, node: Node) -> None:
        """Remove a node from the list."""
        if node._erased:
            warnings.warn(f"Node {node} is already erased", stacklevel=1)
            return
        assert (
            node._graph is self._graph
        ), "Bug: Invariance violation: node is not in the graph"
        # We mark the node as erased instead of removing it from the list,
        # because removing a node from the list during iteration is not safe.
        node._erased = True
        # Remove the node from the graph
        node._graph = None
        self._length -= 1

    def insert_after(self, node: Node, new_nodes: Sequence[Node]) -> None:
        """Insert new nodes after the given node."""
        if len(new_nodes) == 0:
            return
        # Create a doubly linked list of new nodes by establishing the next and prev pointers
        _connect_node_sequence(new_nodes)
        next_node = node._next

        # Insert the new nodes between the node and the next node
        _connect_nodes(node, new_nodes[0])
        _connect_nodes(new_nodes[-1], next_node)

        # Assign graph
        for new_node in new_nodes:
            new_node._graph = self._graph
            # Bring the node back in case it was erased
            new_node._erased = False

        # Update the tail if needed
        if self._tail is node:
            # The node is the last node in the list
            self._tail = new_nodes[-1]

        self._length += len(new_nodes)

        # We don't need to update the head because any of the new nodes cannot be the head

    def insert_before(self, node: Node, new_nodes: Sequence[Node]) -> None:
        """Insert new nodes before the given node."""
        if len(new_nodes) == 0:
            return
        # Create a doubly linked list of new nodes by establishing the next and prev pointers
        _connect_node_sequence(new_nodes)
        prev_node = node._prev

        # Insert the new nodes between the prev node and the node
        _connect_nodes(prev_node, new_nodes[0])
        _connect_nodes(new_nodes[-1], node)

        # Assign graph
        for new_node in new_nodes:
            new_node._graph = self._graph
            # Bring the node back in case it was erased
            new_node._erased = False

        # Update the head if needed
        if self._head is node:
            # The node is the first node in the list
            self._head = new_nodes[0]

        self._length += len(new_nodes)

        # We don't need to update the tail because any of the new nodes cannot be the tail
