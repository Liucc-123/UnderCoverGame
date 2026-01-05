"""
File: nodes.py
Created Time: 2026-01-05
Author: falcon (liuc47810@gmail.com)

LangGraph 节点函数
"""

from .types import GameState, GameStatus, UnderCoverGameManager, PlayerRole, PlayerType
from src.agents.llm import llm


def start_round_node(state: GameState) -> GameState:
    """开始新的回合"""
    # 重置回合数据
    state["current_round"] = state["current_round"] + 1
    state["game_status"] = GameStatus.ROUND_SPEECH
    state["round_speech"] = {}
    state["round_votes"] = {}
    # 重置每个玩家的数据
    for player in state["players"]:
        if player.is_alive:
            player.reset_round()

    print("=" * 60)
    print(f"第 {state["current_round"]} 回合开始！！")
    print("=" * 60)
    print(f"场上存活玩家有: {",".join(p.name for p in state['players'])}")

    return state


def collect_speech_node(state: GameState) -> GameState:
    """收集场上玩家发言"""
    manager = UnderCoverGameManager()
    print("\n【玩家发言阶段】\n")

    player_speeches: dict[int, str] = {}
    for player in state["players"]:
        if not player.is_alive:
            continue

        if player.player_type == PlayerType.HUMAN:
            print(f"\n{player.name}，请用一句话描述你的词语（不能说出词语本身）：")
            human_speech = input("> ").strip()
            if not human_speech:
                human_speech = "水一波，过～"
            player_speeches[player.id] = human_speech

        else:
            # AI生成玩家描述
            prompt = manager.get_player_speech_prompt(player)
            response = llm.invoke(prompt)
            print(f"{player.name} 的发言: {response.content}")
            player_speeches[player.id] = response.content
    state["round_speech"] = player_speeches
    return state


def collect_vote_node(state: GameState) -> GameState:
    """玩家投票节点"""
    state["game_status"] = GameStatus.ROUND_VOTING
    all_players = state["players"]
    manager = UnderCoverGameManager()
    print("\n【玩家投票阶段】\n")
    # 玩家投票收集器
    player_votes: dict[int, int] = {}
    # 场上存活玩家id
    alive_players: list[int] = [player.id for player in all_players if player.is_alive]

    # 投票
    for player in all_players:
        if player.id not in alive_players:
            continue

        # 人类玩家投票
        if player.player_type == PlayerType.HUMAN:
            print(f"{player.name} 您想投票给谁？目前场上仍存活的玩家有:\n")
            for player_id in alive_players:
                print(f"玩家({player_id})")
            vote_for_id = int(input("请输入玩家编号 > "))
        else:
            # AI玩家投票
            prompt = manager.get_player_vote_prompt(player, state["round_speech"], alive_players)
            response = llm.invoke(prompt)
            vote_for_id = int(response.content)
            print(f"{player.name}的投票结果是 {vote_for_id}")
        player_votes[player.id] = vote_for_id
    
    # 更新状态
    state["round_votes"] = player_votes
    return state

def 
                
            

