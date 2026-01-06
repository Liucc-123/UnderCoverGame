"""
File: builder.py
Created Time: 2026-01-05
Author: falcon (liuc47810@gmail.com)
"""

from .types import GameState, PlayerRole, PlayerType
from .nodes import (
    start_round_node, game_end_node, collect_vote_node,
    check_game_end_node, collect_speech_node, process_elimination_node
)
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

# ==================== 条件边界函数 ====================
def should_continue_game(state: GameState) -> Literal["continue_round", "end_game"]:
    """检查游戏是否继续"""
    alive_players = [player for player in state["players"] if player.is_alive]
    undercovers = [
        player
        for player in alive_players
        if player.player_role == PlayerRole.UNDERCOVER
    ]

    # 判定游戏是否继续
    if len(undercovers) == 0:
        return "end_game"
    elif len(alive_players) <= 2:
        return "end_game"
    else:
        return "continue_round"

# ==================== 构建LangGraph ====================
def build_game_graph() -> CompiledStateGraph:
    """构建游戏流程"""
    gameflow = StateGraph(GameState)

    # 添加节点
    gameflow.add_node("start_round", start_round_node)
    gameflow.add_node("collect_speech", collect_speech_node)
    gameflow.add_node("collect_vote", collect_vote_node)
    gameflow.add_node("process_elimination", process_elimination_node)
    gameflow.add_node("check_game_end", check_game_end_node)
    gameflow.add_node("game_end", game_end_node)

    # 添加边
    gameflow.add_edge(START, "start_round")
    gameflow.add_edge("start_round", "collect_speech")
    gameflow.add_edge("collect_speech", "collect_vote")
    gameflow.add_edge("collect_vote", "process_elimination")
    gameflow.add_edge("process_elimination", "check_game_end")

    # 添加条件边，判断是否继续游戏
    gameflow.add_conditional_edges(
        "check_game_end",
        should_continue_game,
        {
            "end_game": "game_end",
            "continue_round": "start_round"
        }
    )

    gameflow.add_edge("game_end", END)

    return gameflow.compile()