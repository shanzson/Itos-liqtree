from collections import defaultdict

from ILiquidity import *
from LiquidityExceptions import *
from Tree.LiquidityKey import LiquidityKey


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


@dataclass
class LiqNode:
    m_liq: UnsignedDecimal = UnsignedDecimal(0)
    t_liq: UnsignedDecimal = UnsignedDecimal(0)
    subtree_m_liq: UnsignedDecimal = UnsignedDecimal(0)

    token_x_borrow: UnsignedDecimal = UnsignedDecimal(0)
    token_x_subtree_borrow: UnsignedDecimal = UnsignedDecimal(0)
    token_x_fee_rate_snapshot: UnsignedDecimal = UnsignedDecimal(0)
    token_x_cumulative_earned_per_m_liq: UnsignedDecimal = UnsignedDecimal(0)
    token_x_cumulative_earned_per_m_subtree_liq: UnsignedDecimal = UnsignedDecimal(0)

    token_y_borrow: UnsignedDecimal = UnsignedDecimal(0)
    token_y_subtree_borrow: UnsignedDecimal = UnsignedDecimal(0)
    token_y_fee_rate_snapshot: UnsignedDecimal = UnsignedDecimal(0)
    token_y_cumulative_earned_per_m_liq: UnsignedDecimal = UnsignedDecimal(0)
    token_y_cumulative_earned_per_m_subtree_liq: UnsignedDecimal = UnsignedDecimal(0)

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


class LiquidityTree(ILiquidity):
    # region Initialization
    def __init__(self, depth: int, sol_truncation: bool = False):
        self.sol_truncation = sol_truncation

        self.root: LiqNode = LiqNode()
        self.width = (1 << depth)
        self.nodes = defaultdict(LiqNode)

        self.root_key = (self.width << 24) | self.width
        self.nodes[self.root_key] = self.root

        self.token_x_fee_rate_snapshot: UnsignedDecimal = UnsignedDecimal(0)
        self.token_y_fee_rate_snapshot: UnsignedDecimal = UnsignedDecimal(0)

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

    def add_m_liq(self, liq_range: LiqRange, liq: UnsignedDecimal) -> None:
        if liq == UnsignedDecimal("0"):
            raise LiquidityExceptionZeroLiquidity()
        if liq_range.low < UnsignedDecimal("0"):
            raise LiquidityExceptionRangeContainsNegative()
        if liq_range.high < UnsignedDecimal("0"):
            raise LiquidityExceptionRangeContainsNegative()
        if liq_range.low == UnsignedDecimal("0") and liq_range.high == UnsignedDecimal(self.width - 1):
            raise LiquidityExceptionRootRange()
        if liq_range.high >= UnsignedDecimal(self.width):
            raise LiquidityExceptionOversizedRange()
        if liq_range.high < liq_range.low:
            raise LiquidityExceptionRangeHighBelowLow()

        low, high, _, stop_range = LiquidityKey.keys(liq_range.low, liq_range.high, self.width)

        current: int
        node: LiqNode

        if low < stop_range:
            current = low
            node = self.nodes[current]
            self.handle_fee(current, node)

            # Thought calculation was cool, might be useful in refactor
            # m_liq_per_tick: int = liq * (self.width >> low_node.depth)
            m_liq_per_tick: UnsignedDecimal = liq * UnsignedDecimal(current >> 24)
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
                    node.subtree_m_liq += liq * UnsignedDecimal(current >> 24)

                # right propagate
                up, left = LiquidityKey.right_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.subtree_m_liq = self.nodes[left].subtree_m_liq + node.subtree_m_liq + parent.m_liq * UnsignedDecimal(up >> 24)
                current, node = up, parent

        if high < stop_range:
            current = high
            node = self.nodes[current]
            self.handle_fee(current, node)

            m_liq_per_tick: UnsignedDecimal = liq * UnsignedDecimal(current >> 24)
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
                    node.subtree_m_liq += liq * UnsignedDecimal(current >> 24)

                # left propogate
                up, right = LiquidityKey.left_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.subtree_m_liq = self.nodes[right].subtree_m_liq + node.subtree_m_liq + parent.m_liq * UnsignedDecimal(up >> 24)
                current, node = up, parent

        node = self.nodes[current]

        while current != self.root_key:
            up, other = LiquidityKey.generic_up(current)
            parent = self.nodes[up]
            self.handle_fee(up, parent)

            parent.subtree_m_liq = self.nodes[other].subtree_m_liq + node.subtree_m_liq + parent.m_liq * UnsignedDecimal(up >> 24)
            current, node = up, parent

    def remove_m_liq(self, liq_range: LiqRange, liq: UnsignedDecimal) -> None:
        if liq == UnsignedDecimal("0"):
            raise LiquidityExceptionZeroLiquidity()
        if liq_range.low < UnsignedDecimal("0"):
            raise LiquidityExceptionRangeContainsNegative()
        if liq_range.high < UnsignedDecimal("0"):
            raise LiquidityExceptionRangeContainsNegative()
        if liq_range.low == UnsignedDecimal("0") and liq_range.high == UnsignedDecimal(self.width - 1):
            raise LiquidityExceptionRootRange()
        if liq_range.high >= UnsignedDecimal(self.width):
            raise LiquidityExceptionOversizedRange()
        if liq_range.high < liq_range.low:
            raise LiquidityExceptionRangeHighBelowLow()

        low, high, _, stop_range = LiquidityKey.keys(liq_range.low, liq_range.high, self.width)

        current: int
        node: LiqNode

        if low < stop_range:
            current = low
            node = self.nodes[current]
            self.handle_fee(current, node)

            # Thought calculation was cool, might be useful in refactor
            # m_liq_per_tick: int = liq * (self.width >> low_node.depth)
            m_liq_per_tick: UnsignedDecimal = liq * UnsignedDecimal(current >> 24)
            node.m_liq -= liq
            node.subtree_m_liq -= m_liq_per_tick

            if node.t_liq > node.m_liq:
                raise LiquidityExceptionTLiqExceedsMLiq()

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
                    node.subtree_m_liq -= liq * UnsignedDecimal(current >> 24)

                    if node.t_liq > node.m_liq:
                        raise LiquidityExceptionTLiqExceedsMLiq()

                # right propagate
                up, left = LiquidityKey.right_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.subtree_m_liq = self.nodes[left].subtree_m_liq + node.subtree_m_liq + parent.m_liq * UnsignedDecimal(up >> 24)
                current, node = up, parent

        if high < stop_range:
            current = high
            node = self.nodes[current]
            self.handle_fee(current, node)

            m_liq_per_tick: UnsignedDecimal = liq * UnsignedDecimal(current >> 24)
            node.m_liq -= liq
            node.subtree_m_liq -= m_liq_per_tick

            if node.t_liq > node.m_liq:
                raise LiquidityExceptionTLiqExceedsMLiq()

            # left propagate
            current, _ = LiquidityKey.left_up(current)
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.subtree_m_liq -= m_liq_per_tick

            while current < stop_range:
                if LiquidityKey.is_right(current):
                    current = LiquidityKey.left_sibling(current)
                    node = self.nodes[current]
                    self.handle_fee(current, node)

                    node.m_liq -= liq
                    node.subtree_m_liq -= liq * UnsignedDecimal(current >> 24)

                    if node.t_liq > node.m_liq:
                        raise LiquidityExceptionTLiqExceedsMLiq()

                # left propogate
                up, right = LiquidityKey.left_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.subtree_m_liq = self.nodes[right].subtree_m_liq + node.subtree_m_liq + parent.m_liq * UnsignedDecimal(up >> 24)
                current, node = up, parent

        node = self.nodes[current]

        while current != self.root_key:
            up, other = LiquidityKey.generic_up(current)
            parent = self.nodes[up]
            self.handle_fee(up, parent)

            parent.subtree_m_liq = self.nodes[other].subtree_m_liq + node.subtree_m_liq + parent.m_liq * UnsignedDecimal(up >> 24)
            current, node = up, parent

    def add_t_liq(self, liq_range: LiqRange, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        if liq == UnsignedDecimal("0"):
            raise LiquidityExceptionZeroLiquidity()
        if liq_range.low < UnsignedDecimal("0"):
            raise LiquidityExceptionRangeContainsNegative()
        if liq_range.high < UnsignedDecimal("0"):
            raise LiquidityExceptionRangeContainsNegative()
        if liq_range.low == UnsignedDecimal("0") and liq_range.high == UnsignedDecimal(self.width - 1):
            raise LiquidityExceptionRootRange()
        if liq_range.high >= UnsignedDecimal(self.width):
            raise LiquidityExceptionOversizedRange()
        if liq_range.high < liq_range.low:
            raise LiquidityExceptionRangeHighBelowLow()

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

            node_range: UnsignedDecimal = UnsignedDecimal(current >> 24)
            node.token_x_borrow += amount_x / liq_range.width() * node_range
            node.token_x_subtree_borrow += amount_x / liq_range.width() * node_range
            node.token_y_borrow += amount_y / liq_range.width() * node_range
            node.token_y_subtree_borrow += amount_y / liq_range.width() * node_range

            if node.t_liq > node.m_liq:
                raise LiquidityExceptionTLiqExceedsMLiq()

            # right propagate
            current, _ = LiquidityKey.right_up(current)
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.token_x_subtree_borrow += amount_x / liq_range.width() * node_range
            node.token_y_subtree_borrow += amount_y / liq_range.width() * node_range

            while current < stop_range:
                if LiquidityKey.is_left(current):
                    current = LiquidityKey.right_sibling(current)
                    node = self.nodes[current]
                    self.handle_fee(current, node)

                    node.t_liq += liq

                    node_range = UnsignedDecimal(current >> 24)
                    node.token_x_borrow += amount_x / liq_range.width() * node_range
                    node.token_x_subtree_borrow += amount_x / liq_range.width() * node_range
                    node.token_y_borrow += amount_y / liq_range.width() * node_range
                    node.token_y_subtree_borrow += amount_y / liq_range.width() * node_range

                    if node.t_liq > node.m_liq:
                        raise LiquidityExceptionTLiqExceedsMLiq()

                # right propagate
                up, left = LiquidityKey.right_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.token_x_subtree_borrow = self.nodes[left].token_x_subtree_borrow + node.token_x_subtree_borrow + parent.token_x_borrow
                parent.token_y_subtree_borrow = self.nodes[left].token_y_subtree_borrow + node.token_y_subtree_borrow + parent.token_y_borrow
                current, node = up, parent

        if high < stop_range:
            current = high
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.t_liq += liq

            node_range: UnsignedDecimal = UnsignedDecimal(current >> 24)
            node.token_x_borrow += amount_x / liq_range.width() * node_range
            node.token_x_subtree_borrow += amount_x / liq_range.width() * node_range
            node.token_y_borrow += amount_y / liq_range.width() * node_range
            node.token_y_subtree_borrow += amount_y / liq_range.width() * node_range

            if node.t_liq > node.m_liq:
                raise LiquidityExceptionTLiqExceedsMLiq()

            # left propagate
            current, _ = LiquidityKey.left_up(current)
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.token_x_subtree_borrow += amount_x / liq_range.width() * node_range
            node.token_y_subtree_borrow += amount_y / liq_range.width() * node_range

            while current < stop_range:
                if LiquidityKey.is_right(current):
                    current = LiquidityKey.left_sibling(current)
                    node = self.nodes[current]
                    self.handle_fee(current, node)

                    node.t_liq += liq

                    node_range = UnsignedDecimal(current >> 24)
                    node.token_x_borrow += amount_x / liq_range.width() * node_range
                    node.token_x_subtree_borrow += amount_x / liq_range.width() * node_range
                    node.token_y_borrow += amount_y / liq_range.width() * node_range
                    node.token_y_subtree_borrow += amount_y / liq_range.width() * node_range

                    if node.t_liq > node.m_liq:
                        raise LiquidityExceptionTLiqExceedsMLiq()

                # left propogate
                up, right = LiquidityKey.left_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.token_x_subtree_borrow = self.nodes[right].token_x_subtree_borrow + node.token_x_subtree_borrow + parent.token_x_borrow
                parent.token_y_subtree_borrow = self.nodes[right].token_y_subtree_borrow + node.token_y_subtree_borrow + parent.token_y_borrow
                current, node = up, parent

        node = self.nodes[current]

        while current != self.root_key:
            up, other = LiquidityKey.generic_up(current)
            parent = self.nodes[up]
            self.handle_fee(up, parent)

            parent.token_x_subtree_borrow = self.nodes[other].token_x_subtree_borrow + node.token_x_subtree_borrow + parent.token_x_borrow
            parent.token_y_subtree_borrow = self.nodes[other].token_y_subtree_borrow + node.token_y_subtree_borrow + parent.token_y_borrow
            current, node = up, parent

    def remove_t_liq(self, liq_range: LiqRange, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        if liq == UnsignedDecimal("0"):
            raise LiquidityExceptionZeroLiquidity()
        if liq_range.low < UnsignedDecimal("0"):
            raise LiquidityExceptionRangeContainsNegative()
        if liq_range.high < UnsignedDecimal("0"):
            raise LiquidityExceptionRangeContainsNegative()
        if liq_range.low == UnsignedDecimal("0") and liq_range.high == UnsignedDecimal(self.width - 1):
            raise LiquidityExceptionRootRange()
        if liq_range.high >= UnsignedDecimal(self.width):
            raise LiquidityExceptionOversizedRange()
        if liq_range.high < liq_range.low:
            raise LiquidityExceptionRangeHighBelowLow()

        low, high, _, stop_range = LiquidityKey.keys(liq_range.low, liq_range.high, self.width)

        current: int
        node: LiqNode

        if low < stop_range:
            current = low
            node = self.nodes[current]
            self.handle_fee(current, node)

            # Thought calculation was cool, might be useful in refactor
            # m_liq_per_tick: int = liq * (self.width >> low_node.depth)
            node.t_liq = node.t_liq - liq

            node_range: UnsignedDecimal = UnsignedDecimal(current >> 24)
            node.token_x_borrow -= amount_x / liq_range.width() * node_range
            node.token_x_subtree_borrow -= amount_x / liq_range.width() * node_range
            node.token_y_borrow -= amount_y / liq_range.width() * node_range
            node.token_y_subtree_borrow -= amount_y / liq_range.width() * node_range

            # right propagate
            current, _ = LiquidityKey.right_up(current)
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.token_x_subtree_borrow -= amount_x / liq_range.width() * node_range
            node.token_y_subtree_borrow -= amount_y / liq_range.width() * node_range

            while current < stop_range:
                if LiquidityKey.is_left(current):
                    current = LiquidityKey.right_sibling(current)
                    node = self.nodes[current]
                    self.handle_fee(current, node)

                    node.t_liq -= liq

                    node_range = UnsignedDecimal(current >> 24)
                    node.token_x_borrow -= amount_x / liq_range.width() * node_range
                    node.token_x_subtree_borrow -= amount_x / liq_range.width() * node_range
                    node.token_y_borrow -= amount_y / liq_range.width() * node_range
                    node.token_y_subtree_borrow -= amount_y / liq_range.width() * node_range

                # right propagate
                up, left = LiquidityKey.right_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.token_x_subtree_borrow = self.nodes[left].token_x_subtree_borrow + node.token_x_subtree_borrow + parent.token_x_borrow
                parent.token_y_subtree_borrow = self.nodes[left].token_y_subtree_borrow + node.token_y_subtree_borrow + parent.token_y_borrow
                current, node = up, parent

        if high < stop_range:
            current = high
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.t_liq -= liq

            node_range: UnsignedDecimal = UnsignedDecimal(current >> 24)
            node.token_x_borrow -= amount_x / liq_range.width() * node_range
            node.token_x_subtree_borrow -= amount_x / liq_range.width() * node_range
            node.token_y_borrow -= amount_y / liq_range.width() * node_range
            node.token_y_subtree_borrow -= amount_y / liq_range.width() * node_range

            # left propagate
            current, _ = LiquidityKey.left_up(current)
            node = self.nodes[current]
            self.handle_fee(current, node)

            node.token_x_subtree_borrow -= amount_x / liq_range.width() * node_range
            node.token_y_subtree_borrow -= amount_y / liq_range.width() * node_range

            while current < stop_range:
                if LiquidityKey.is_right(current):
                    current = LiquidityKey.left_sibling(current)
                    node = self.nodes[current]
                    self.handle_fee(current, node)

                    node.t_liq -= liq

                    node_range = UnsignedDecimal(current >> 24)
                    node.token_x_borrow -= amount_x / liq_range.width() * node_range
                    node.token_x_subtree_borrow -= amount_x / liq_range.width() * node_range
                    node.token_y_borrow -= amount_y / liq_range.width() * node_range
                    node.token_y_subtree_borrow -= amount_y / liq_range.width() * node_range

                # left propogate
                up, right = LiquidityKey.left_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)

                parent.token_x_subtree_borrow = self.nodes[right].token_x_subtree_borrow + node.token_x_subtree_borrow + parent.token_x_borrow
                parent.token_y_subtree_borrow = self.nodes[right].token_y_subtree_borrow + node.token_y_subtree_borrow + parent.token_y_borrow
                current, node = up, parent

        node = self.nodes[current]

        while current != self.root_key:
            up, other = LiquidityKey.generic_up(current)
            parent = self.nodes[up]
            self.handle_fee(up, parent)

            parent.token_x_subtree_borrow = self.nodes[other].token_x_subtree_borrow + node.token_x_subtree_borrow + parent.token_x_borrow
            parent.token_y_subtree_borrow = self.nodes[other].token_y_subtree_borrow + node.token_y_subtree_borrow + parent.token_y_borrow
            current, node = up, parent

    # endregion

    def handle_fee(self, current: int, node: LiqNode):
        token_x_fee_rate_diff: UnsignedDecimal = self.token_x_fee_rate_snapshot - node.token_x_fee_rate_snapshot
        node.token_x_fee_rate_snapshot = self.token_x_fee_rate_snapshot
        token_y_fee_rate_diff: UnsignedDecimal = self.token_y_fee_rate_snapshot - node.token_y_fee_rate_snapshot
        node.token_y_fee_rate_snapshot = self.token_y_fee_rate_snapshot

        aux_level: UnsignedDecimal = (0 if current == self.root_key else self.auxiliary_level_m_liq(current))
        total_m_liq: UnsignedDecimal = node.subtree_m_liq + aux_level * UnsignedDecimal(current >> 24)

        if total_m_liq <= 0:
            return

        node.token_x_cumulative_earned_per_m_liq += node.token_x_borrow * token_x_fee_rate_diff / total_m_liq / TWO_POW_SIXTY_FOUR
        node.token_x_cumulative_earned_per_m_subtree_liq += node.token_x_subtree_borrow * token_x_fee_rate_diff / total_m_liq / TWO_POW_SIXTY_FOUR

        node.token_y_cumulative_earned_per_m_liq += node.token_y_borrow * token_y_fee_rate_diff / total_m_liq / TWO_POW_SIXTY_FOUR
        node.token_y_cumulative_earned_per_m_subtree_liq += node.token_y_subtree_borrow * token_y_fee_rate_diff / total_m_liq / TWO_POW_SIXTY_FOUR

        if self.sol_truncation:
            node.token_x_cumulative_earned_per_m_liq = UnsignedDecimal(int(node.token_x_cumulative_earned_per_m_liq))
            node.token_x_cumulative_earned_per_m_subtree_liq = UnsignedDecimal(int(node.token_x_cumulative_earned_per_m_subtree_liq))

            node.token_y_cumulative_earned_per_m_liq = UnsignedDecimal(int(node.token_y_cumulative_earned_per_m_liq))
            node.token_y_cumulative_earned_per_m_subtree_liq = UnsignedDecimal(int(node.token_y_cumulative_earned_per_m_subtree_liq))

    def auxiliary_level_m_liq(self, node_key: int) -> UnsignedDecimal:
        if node_key == self.root_key:
            return UnsignedDecimal(0)

        m_liq: UnsignedDecimal = UnsignedDecimal(0)
        node_key, _ = LiquidityKey.generic_up(node_key)
        while node_key < self.root_key:
            m_liq += self.nodes[node_key].m_liq
            node_key, _ = LiquidityKey.generic_up(node_key)

        m_liq += self.root.m_liq
        return m_liq

    def query_min_m_liq_max_t_liq(self, liq_range: LiqRange) -> (UnsignedDecimal, UnsignedDecimal):
        """Returns the min mLiq, max tLiq over the wide range. Returned liquidity is per tick."""
        raise NotImplementedError

    def query_wide_min_m_liq_max_t_liq(self) -> (UnsignedDecimal, UnsignedDecimal):
        """Returns the min mLiq, max tLiq over the wide range. Returned liquidity is for all tick."""
        raise NotImplementedError

    def query_accumulated_fee_rates(self, liq_range: LiqRange) -> (UnsignedDecimal, UnsignedDecimal):
        """Returns the accumulated fee rates per mLiq for each token over the provided range."""
        acc_rate_x = acc_rate_y = UnsignedDecimal(0)

        low, high, _, stop_range = LiquidityKey.keys(liq_range.low, liq_range.high, self.width)

        current: int
        node: LiqNode

        if low < stop_range:
            current = low
            node = self.nodes[current]
            self.handle_fee(current, node)

            acc_rate_x += node.token_x_cumulative_earned_per_m_subtree_liq
            acc_rate_y += node.token_y_cumulative_earned_per_m_subtree_liq

            # right propagate
            current, _ = LiquidityKey.right_up(current)
            node = self.nodes[current]
            self.handle_fee(current, node)

            acc_rate_x += node.token_x_cumulative_earned_per_m_liq
            acc_rate_y += node.token_y_cumulative_earned_per_m_liq

            while current < stop_range:
                if LiquidityKey.is_left(current):
                    current = LiquidityKey.right_sibling(current)
                    node = self.nodes[current]
                    self.handle_fee(current, node)

                    acc_rate_x += node.token_x_cumulative_earned_per_m_subtree_liq
                    acc_rate_y += node.token_y_cumulative_earned_per_m_subtree_liq

                # right propagate
                up, left = LiquidityKey.right_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)
                current, node = up, parent

                acc_rate_x += node.token_x_cumulative_earned_per_m_liq
                acc_rate_y += node.token_y_cumulative_earned_per_m_liq

        if high < stop_range:
            current = high
            node = self.nodes[current]
            self.handle_fee(current, node)

            acc_rate_x += node.token_x_cumulative_earned_per_m_subtree_liq
            acc_rate_y += node.token_y_cumulative_earned_per_m_subtree_liq

            # left propagate
            current, _ = LiquidityKey.left_up(current)
            node = self.nodes[current]
            self.handle_fee(current, node)

            acc_rate_x += node.token_x_cumulative_earned_per_m_liq
            acc_rate_y += node.token_y_cumulative_earned_per_m_liq

            while current < stop_range:
                if LiquidityKey.is_right(current):
                    current = LiquidityKey.left_sibling(current)
                    node = self.nodes[current]
                    self.handle_fee(current, node)

                    acc_rate_x += node.token_x_cumulative_earned_per_m_subtree_liq
                    acc_rate_y += node.token_y_cumulative_earned_per_m_subtree_liq

                # left propogate
                up, right = LiquidityKey.left_up(current)
                parent = self.nodes[up]
                self.handle_fee(up, parent)
                current, node = up, parent

                acc_rate_x += node.token_x_cumulative_earned_per_m_liq
                acc_rate_y += node.token_y_cumulative_earned_per_m_liq

        node = self.nodes[current]

        while current != self.root_key:
            up, other = LiquidityKey.generic_up(current)
            parent = self.nodes[up]
            self.handle_fee(up, parent)
            current, node = up, parent

            acc_rate_x += node.token_x_cumulative_earned_per_m_liq
            acc_rate_y += node.token_y_cumulative_earned_per_m_liq

        return acc_rate_x, acc_rate_y

    def query_wide_accumulated_fee_rates(self) -> (UnsignedDecimal, UnsignedDecimal):
        """Returns the accumulated fee rates per mLiq for each token over the wide range."""
        raise NotImplementedError

    # region Liquidity Wide Range Methods

    def add_wide_m_liq(self, liq: UnsignedDecimal) -> None:
        self.handle_fee(self.root_key, self.root)

        self.root.m_liq += liq
        self.root.subtree_m_liq += self.width * liq

    def remove_wide_m_liq(self, liq: UnsignedDecimal) -> None:
        self.handle_fee(self.root_key, self.root)

        self.root.m_liq -= liq
        self.root.subtree_m_liq -= self.width * liq

    def add_wide_t_liq(self, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        self.handle_fee(self.root_key, self.root)

        self.root.t_liq += liq
        self.root.token_x_borrow += amount_x
        self.root.token_x_subtree_borrow += amount_x
        self.root.token_y_borrow += amount_y
        self.root.token_y_subtree_borrow += amount_y

    def remove_wide_t_liq(self, liq: UnsignedDecimal, amount_x: UnsignedDecimal, amount_y: UnsignedDecimal) -> None:
        self.handle_fee(self.root_key, self.root)

        self.root.t_liq -= liq
        self.root.token_x_borrow -= amount_x
        self.root.token_x_subtree_borrow -= amount_x
        self.root.token_y_borrow -= amount_y
        self.root.token_y_subtree_borrow -= amount_y

    # endregion
