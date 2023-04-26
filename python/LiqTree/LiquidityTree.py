from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from LiqTree.LiquidityKey import LiquidityKey


#  Liquidity Tree
#
#  Consider a tree with a depth of 4
#
#                                                               root
#                                                       ____----    ----____
#                                   __________----------                    ----------__________
#                                  L                                                            R
#                             __--  --__                                                    __--  --__
#                        __---          ---__                                          __---          ---__
#                      /                       \                                     /                       \
#                   LL                           LR                               RL                           RR
#                 /   \                         /   \                           /   \                         /   \
#               /       \                     /       \                       /       \                     /       \
#             /           \                 /           \                   /           \                 /           \
#           LLL            LLR            LRL            LRR              RLL            RLR            RRL            RRR
#          /   \          /   \          /   \          /   \            /   \          /   \          /   \          /   \
#         /     \        /     \        /     \        /     \          /     \        /     \        /     \        /     \
#      LLLL    LLLR    LLRL    LLRR   LRLL    LRLR   LRRL    LRRR      RLLL   RLLR   RLRL    RLRR   RRLL    RRLR   RRRL    RRRR

TWO_POW_SIXTY_FOUR: Decimal = Decimal(2**64)


@dataclass
class LiqRange:
    low: int
    high: int


@dataclass
class LiqNode:
    m_liq: Decimal = Decimal(0)
    t_liq: Decimal = Decimal(0)
    subtree_m_liq: Decimal = Decimal(0)

    token_x_borrowed: Decimal = Decimal(0)
    token_x_subtree_borrowed: Decimal = Decimal(0)
    token_x_fee_rate_snapshot: Decimal = Decimal(0)
    token_x_cummulative_earned_per_m_liq: Decimal = Decimal(0)
    token_x_cummulative_earned_per_m_subtree_liq: Decimal = Decimal(0)

    token_y_borrowed: Decimal = Decimal(0)
    token_y_subtree_borrowed: Decimal = Decimal(0)
    token_y_fee_rate_snapshot: Decimal = Decimal(0)
    token_y_cummulative_earned_per_m_liq: Decimal = Decimal(0)
    token_y_cummulative_earned_per_m_subtree_liq: Decimal = Decimal(0)

    # Can think of node in a tree as the combination key of (value, base)
    # ex. R is (1, 1) while LRR is (3, 2)
    # value is the nodes binary value. If in the tree 0 is prepended for a left traversal, and a 1 for a right traversal
    # value: int = 0
    # depth: int = 0
    # liq_key: int = 0
    #
    # parent = None
    # left = None
    # right = None


class LiquidityTree:
    # region Initialization
    def __init__(self, depth: int):
        self.root: LiqNode = LiqNode()
        self.width = (1 << depth)
        self.nodes = defaultdict(LiqNode)

        self.root_key = (self.width << 24) | self.width
        self.nodes[self.root_key] = self.root

        self.token_x_fee_rate_snapshot: Decimal = Decimal(0)
        self.token_y_fee_rate_snapshot: Decimal = Decimal(0)

        # self._init_tree(self.root, None, 0, 0, depth)

    # def _init_tree(self, current: LiqNode, parent: LiqNode, value: int, depth: int, max_depth: int) -> None:
    #     current.parent = parent
    #
    #     if depth > max_depth:
    #         return
    #
    #     left: LiqNode = LiqNode()
    #     left.depth = depth
    #     left.value = (0 << depth) + value
    #     left.liq_key = 0
    #     current.left = left
    #
    #     right: LiqNode = LiqNode()
    #     right.depth = depth
    #     right.value = (1 << depth) + value
    #     right.liq_key = 0
    #     current.right = right
    #
    #     self._init_tree(left, current, depth + 1, max_depth)
    #     self._init_tree(right, current, depth + 1, max_depth)

    # endregion

    # region Liquidity Limited Range Methods

    def add_m_liq(self, liq_range: LiqRange, liq: Decimal) -> None:
        low, high, _, stop_range = LiquidityKey.keys(liq_range.low, liq_range.high, self.width)

        current: int
        node: LiqNode

        if low < stop_range:
            current = low
            node = self.nodes[current]
            self.handle_fee(current, node)

            # Thought calculation was cool, might be useful in refactor
            # m_liq_per_tick: int = liq * (self.width >> low_node.depth)
            m_liq_per_tick: Decimal = liq * Decimal(current >> 24)
            node.m_liq += liq
            node.subtree_m_liq += m_liq_per_tick

            # right propagate
            current, _ = LiquidityKey.right_up(current)
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.subtree_m_liq += m_liq_per_tick

            while current < stop_range:
                if LiquidityKey.is_left(current):
                    current = LiquidityKey.right_sibling(current)
                    node = self.nodes[current]
                    self.handle_fee(current, node)

                    node.m_liq += liq
                    node.subtree_m_liq += liq * Decimal(current >> 24)

                # right propagate
                up, left = LiquidityKey.right_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.subtree_m_liq = self.nodes[left].subtree_m_liq + node.subtree_m_liq + parent.m_liq * Decimal(up >> 24)
                current, node = up, parent

        if high < stop_range:
            current = high
            node = self.nodes[current]
            self.handle_fee(current, node)

            m_liq_per_tick: Decimal = liq * Decimal(current >> 24)
            node.m_liq += liq
            node.subtree_m_liq += m_liq_per_tick

            # left propagate
            current, _ = LiquidityKey.left_up(current)
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.subtree_m_liq += m_liq_per_tick

            while current < stop_range:
                if LiquidityKey.is_right(current):
                    current = LiquidityKey.left_sibling(current)
                    node = self.nodes[current]
                    self.handle_fee(current, node)

                    node.m_liq += liq
                    node.subtree_m_liq += liq * Decimal(current >> 24)

                # left propogate
                up, right = LiquidityKey.left_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.subtree_m_liq = self.nodes[right].subtree_m_liq + node.subtree_m_liq + parent.m_liq * Decimal(up >> 24)
                current, node = up, parent

            node = self.nodes[current]

            while current < self.root_key:
                up, other = LiquidityKey.generic_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.subtree_m_liq = self.nodes[other].subtree_m_liq + node.subtree_m_liq + parent.m_liq * Decimal(up >> 24)
                current, node = up, parent

    def remove_m_liq(self, liq_range: LiqRange, liq: Decimal) -> None:
        low, high, _, stop_range = LiquidityKey.keys(liq_range.low, liq_range.high, self.width)

        current: int
        node: LiqNode

        if low < stop_range:
            current = low
            node = self.nodes[current]
            self.handle_fee(current, node)

            # Thought calculation was cool, might be useful in refactor
            # m_liq_per_tick: int = liq * (self.width >> low_node.depth)
            m_liq_per_tick: Decimal = liq * Decimal(current >> 24)
            node.m_liq -= liq
            node.subtree_m_liq -= m_liq_per_tick

            # right propagate
            current, _ = LiquidityKey.right_up(current)
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.subtree_m_liq -= m_liq_per_tick

            while current < stop_range:
                if LiquidityKey.is_left(current):
                    current = LiquidityKey.right_sibling(current)
                    node = self.nodes[current]
                    self.handle_fee(current, node)

                    node.m_liq -= liq
                    node.subtree_m_liq -= liq * Decimal(current >> 24)

                # right propagate
                up, left = LiquidityKey.right_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.subtree_m_liq = self.nodes[left].subtree_m_liq + node.subtree_m_liq + parent.m_liq * Decimal(up >> 24)
                current, node = up, parent

        if high < stop_range:
            current = high
            node = self.nodes[current]
            self.handle_fee(current, node)

            m_liq_per_tick: Decimal = liq * Decimal(current >> 24)
            node.m_liq -= liq
            node.subtree_m_liq -= m_liq_per_tick

            # left propagate
            current, _ = LiquidityKey.left_up(current)
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.subtree_m_liq += m_liq_per_tick

            while current < stop_range:
                if LiquidityKey.is_right(current):
                    current = LiquidityKey.left_sibling(current)
                    node = self.nodes[current]
                    self.handle_fee(current, node)

                    node.m_liq -= liq
                    node.subtree_m_liq -= liq * Decimal(current >> 24)

                # left propogate
                up, right = LiquidityKey.left_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.subtree_m_liq = self.nodes[right].subtree_m_liq + node.subtree_m_liq + parent.m_liq * Decimal(up >> 24)
                current, node = up, parent

            node = self.nodes[current]

            while current < self.root_key:
                up, other = LiquidityKey.generic_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.subtree_m_liq = self.nodes[other].subtree_m_liq + node.subtree_m_liq + parent.m_liq * Decimal(up >> 24)
                current, node = up, parent

    def add_t_liq(self, liq_range: LiqRange, liq: Decimal, amount_x: Decimal, amount_y: Decimal) -> None:
        low, high, _, stop_range = LiquidityKey.keys(liq_range.low, liq_range.high, self.width)

        current: int
        node: LiqNode

        if low < stop_range:
            current = low
            node = self.nodes[current]
            self.handle_fee(current, node)

            # Thought calculation was cool, might be useful in refactor
            # m_liq_per_tick: int = liq * (self.width >> low_node.depth)
            node.t_liq += liq
            node.token_x_borrowed += amount_x
            node.token_y_borrowed += amount_y
            node.token_x_subtree_borrowed += amount_x
            node.token_y_subtree_borrowed += amount_y

            # right propagate
            current, _ = LiquidityKey.right_up(current)
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.token_x_subtree_borrowed += amount_x
            node.token_y_subtree_borrowed += amount_y

            while current < stop_range:
                if LiquidityKey.is_left(current):
                    current = LiquidityKey.right_sibling(current)
                    node = self.nodes[current]
                    self.handle_fee(current, node)

                    node.t_liq += liq
                    node.token_x_borrowed += amount_x
                    node.token_y_borrowed += amount_y
                    node.token_x_subtree_borrowed += amount_x
                    node.token_y_subtree_borrowed += amount_y

                # right propagate
                up, left = LiquidityKey.right_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.token_x_subtree_borrowed += self.nodes[left].token_x_subtree_borrowed + node.token_x_subtree_borrowed + parent.token_x_borrowed
                parent.token_y_subtree_borrowed += self.nodes[left].token_y_subtree_borrowed + node.token_y_subtree_borrowed + parent.token_y_borrowed
                current, node = up, parent

        if high < stop_range:
            current = high
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.t_liq += liq
            node.token_x_borrowed += amount_x
            node.token_y_borrowed += amount_y
            node.token_x_subtree_borrowed += amount_x
            node.token_y_subtree_borrowed += amount_y

            # left propagate
            current, _ = LiquidityKey.left_up(current)
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.token_x_subtree_borrowed += amount_x
            node.token_y_subtree_borrowed += amount_y

            while current < stop_range:
                if LiquidityKey.is_right(current):
                    current = LiquidityKey.left_sibling(current)
                    node = self.nodes[current]
                    self.handle_fee(current, node)

                    node.t_liq += liq
                    node.token_x_borrowed += amount_x
                    node.token_y_borrowed += amount_y
                    node.token_x_subtree_borrowed += amount_x
                    node.token_y_subtree_borrowed += amount_y

                # left propogate
                up, right = LiquidityKey.left_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.token_x_subtree_borrowed += self.nodes[left].token_x_subtree_borrowed + node.token_x_subtree_borrowed + parent.token_x_borrowed
                parent.token_y_subtree_borrowed += self.nodes[left].token_y_subtree_borrowed + node.token_y_subtree_borrowed + parent.token_y_borrowed
                current, node = up, parent

            node = self.nodes[current]

            while current < self.root_key:
                up, other = LiquidityKey.generic_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.token_x_subtree_borrowed += self.nodes[other].token_x_subtree_borrowed + node.token_x_subtree_borrowed + parent.token_x_borrowed
                parent.token_y_subtree_borrowed += self.nodes[other].token_y_subtree_borrowed + node.token_y_subtree_borrowed + parent.token_y_borrowed
                current, node = up, parent

    def remove_t_liq(self, liq_range: LiqRange, liq: Decimal, amount_x: Decimal, amount_y: Decimal) -> None:
        low, high, _, stop_range = LiquidityKey.keys(liq_range.low, liq_range.high, self.width)

        current: int
        node: LiqNode

        if low < stop_range:
            current = low
            node = self.nodes[current]
            self.handle_fee(current, node)

            # Thought calculation was cool, might be useful in refactor
            # m_liq_per_tick: int = liq * (self.width >> low_node.depth)
            node.t_liq -= liq
            node.token_x_borrowed -= amount_x
            node.token_y_borrowed -= amount_y
            node.token_x_subtree_borrowed -= amount_x
            node.token_y_subtree_borrowed -= amount_y

            # right propagate
            current, _ = LiquidityKey.right_up(current)
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.token_x_subtree_borrowed -= amount_x
            node.token_y_subtree_borrowed -= amount_y

            while current < stop_range:
                if LiquidityKey.is_left(current):
                    current = LiquidityKey.right_sibling(current)
                    node = self.nodes[current]
                    self.handle_fee(current, node)

                    node.t_liq -= liq
                    node.token_x_borrowed -= amount_x
                    node.token_y_borrowed -= amount_y
                    node.token_x_subtree_borrowed -= amount_x
                    node.token_y_subtree_borrowed -= amount_y

                # right propagate
                up, left = LiquidityKey.right_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.token_x_subtree_borrowed += self.nodes[left].token_x_subtree_borrowed + node.token_x_subtree_borrowed + parent.token_x_borrowed
                parent.token_y_subtree_borrowed += self.nodes[left].token_y_subtree_borrowed + node.token_y_subtree_borrowed + parent.token_y_borrowed
                current, node = up, parent

        if high < stop_range:
            current = high
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.t_liq += liq
            node.token_x_borrowed -= amount_x
            node.token_y_borrowed -= amount_y
            node.token_x_subtree_borrowed -= amount_x
            node.token_y_subtree_borrowed -= amount_y

            # left propagate
            current, _ = LiquidityKey.left_up(current)
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.token_x_subtree_borrowed -= amount_x
            node.token_y_subtree_borrowed -= amount_y

            while current < stop_range:
                if LiquidityKey.is_right(current):
                    current = LiquidityKey.left_sibling(current)
                    node = self.nodes[current]
                    self.handle_fee(current, node)

                    node.t_liq -= liq
                    node.token_x_borrowed -= amount_x
                    node.token_y_borrowed -= amount_y
                    node.token_x_subtree_borrowed -= amount_x
                    node.token_y_subtree_borrowed -= amount_y

                # left propogate
                up, right = LiquidityKey.left_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.token_x_subtree_borrowed += self.nodes[left].token_x_subtree_borrowed + node.token_x_subtree_borrowed + parent.token_x_borrowed
                parent.token_y_subtree_borrowed += self.nodes[left].token_y_subtree_borrowed + node.token_y_subtree_borrowed + parent.token_y_borrowed
                current, node = up, parent

            node = self.nodes[current]

            while current < self.root_key:
                up, other = LiquidityKey.generic_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.token_x_subtree_borrowed += self.nodes[other].token_x_subtree_borrowed + node.token_x_subtree_borrowed + parent.token_x_borrowed
                parent.token_y_subtree_borrowed += self.nodes[other].token_y_subtree_borrowed + node.token_y_subtree_borrowed + parent.token_y_borrowed
                current, node = up, parent

    # endregion

    def handle_fee(self, current: int, node: LiqNode):
        token_x_fee_rate_diff: Decimal = self.token_x_fee_rate_snapshot - node.token_x_fee_rate_snapshot
        token_y_fee_rate_diff: Decimal = self.token_y_fee_rate_snapshot - node.token_y_fee_rate_snapshot
        node.token_x_fee_rate_snapshot = self.token_x_fee_rate_snapshot
        node.token_y_fee_rate_snapshot = self.token_y_fee_rate_snapshot

        aux_level: Decimal = self.auxiliary_level_m_liq(current)
        total_m_liq: Decimal = node.subtree_m_liq + aux_level * Decimal(current >> 24)

        if total_m_liq <= 0:
            return

        node.token_x_cummulative_earned_per_m_liq += node.token_x_borrowed * token_x_fee_rate_diff / total_m_liq / TWO_POW_SIXTY_FOUR
        node.token_x_cummulative_earned_per_m_subtree_liq += node.token_x_subtree_borrowed * token_x_fee_rate_diff / total_m_liq / TWO_POW_SIXTY_FOUR
        node.token_y_cummulative_earned_per_m_liq += node.token_y_borrowed * token_y_fee_rate_diff / total_m_liq / TWO_POW_SIXTY_FOUR
        node.token_y_cummulative_earned_per_m_subtree_liq += node.token_y_subtree_borrowed * token_y_fee_rate_diff / total_m_liq / TWO_POW_SIXTY_FOUR

    def handle_root_fee(self):
        token_x_fee_rate_diff: Decimal = self.token_x_fee_rate_snapshot - self.root.token_x_fee_rate_snapshot
        token_y_fee_rate_diff: Decimal = self.token_y_fee_rate_snapshot - self.root.token_y_fee_rate_snapshot
        self.root.token_x_fee_rate_snapshot = self.token_x_fee_rate_snapshot
        self.root.token_y_fee_rate_snapshot = self.token_y_fee_rate_snapshot

        total_m_liq: Decimal = self.root.subtree_m_liq

        if total_m_liq <= 0:
            return

        self.root.token_x_cummulative_earned_per_m_liq += self.root.token_x_borrowed * token_x_fee_rate_diff / total_m_liq / TWO_POW_SIXTY_FOUR
        self.root.token_x_cummulative_earned_per_m_subtree_liq += self.root.token_x_subtree_borrowed * token_x_fee_rate_diff / total_m_liq / TWO_POW_SIXTY_FOUR
        self.root.token_y_cummulative_earned_per_m_liq += self.root.token_y_borrowed * token_y_fee_rate_diff / total_m_liq / TWO_POW_SIXTY_FOUR
        self.root.token_y_cummulative_earned_per_m_subtree_liq += self.root.token_y_subtree_borrowed * token_y_fee_rate_diff / total_m_liq / TWO_POW_SIXTY_FOUR

    def auxiliary_level_m_liq(self, node_key: int) -> Decimal:
        node: LiqNode = self.nodes[node_key]
        if node == self.root:
            return Decimal(0)

        m_liq: Decimal = Decimal(0)
        while node_key < self.root_key:
            m_liq += node.m_liq

            # move to parent
            node_key, _ = LiquidityKey.generic_up(node_key)
            node = self.nodes[node_key]

        m_liq += self.root.m_liq
        return m_liq


    # region Liquidity INF Range Methods

    def add_inf_range_m_liq(self, liq: Decimal) -> None:
        self.handle_root_fee()

        self.root.m_liq += liq
        self.root.subtree_m_liq += self.width * liq

    def remove_inf_range_m_liq(self, liq: Decimal) -> None:
        self.handle_root_fee()

        self.root.m_liq -= liq
        self.root.subtree_m_liq -= self.width * liq

    def add_inf_range_t_liq(self, liq: Decimal, amount_x: Decimal, amount_y: Decimal) -> None:
        self.handle_root_fee()

        self.root.t_liq += liq
        self.root.token_x_borrowed += amount_x
        self.root.token_x_subtree_borrowed += amount_x
        self.root.token_y_borrowed += amount_y
        self.root.token_y_subtree_borrowed += amount_y

    def remove_inf_range_t_liq(self, liq: Decimal, amount_x: Decimal, amount_y: Decimal) -> None:
        self.handle_root_fee()

        self.root.t_liq -= liq
        self.root.token_x_borrowed -= amount_x
        self.root.token_x_subtree_borrowed -= amount_x
        self.root.token_y_borrowed -= amount_y
        self.root.token_y_subtree_borrowed -= amount_y

    # endregion
