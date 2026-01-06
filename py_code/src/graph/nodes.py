"""
File: nodes.py
Created Time: 2026-01-05
Author: falcon (liuc47810@gmail.com)
LangGraph 节点函数
"""
from .types import (
    GameState,
    GameStatus,
    UnderCoverGameManager,
    PlayerRole,
    PlayerType,
    Player,
)
from src.agents.llm import llm


def start_round_node(state: GameState) -> GameState:
    """开始新的回合"""
    # 重置回合数据
    state["game_status"] = GameStatus.ROUND_SPEECH
    state["round_speech"] = {}
    state["round_votes"] = {}
    all_players = state["players"]
    alive_players = [player for player in all_players if player.is_alive]
    # 重置每个存活玩家的数据
    for player in alive_players:
        player.reset_round()

    print("=" * 60)
    print(f"第 {state['current_round']} 回合开始！")
    print("=" * 60)
    print(f"场上存活玩家有：{','.join(p.name for p in alive_players)}")

    return state


def collect_speech_node(state: GameState) -> GameState:
    """收集场上玩家发言"""
    manager = UnderCoverGameManager()
    print("\n【玩家发言阶段】")

    player_speeches: dict[int, str] = {}
    for player in state["players"]:
        if not player.is_alive:
            continue

        if player.player_type == PlayerType.HUMAN:
            print(f"\n{player.name}，请用一句话描述你的词语（不能说出词语本身）：")
            human_speech = input("> ").strip()
            if not human_speech:
                human_speech = "水一波，过~"
            player_speeches[player.id] = human_speech
            print(f"玩家【{player.id}】{player.name}】发言：{human_speech}")
        else:
            # AI生成玩家描述
            # 已发言玩家
            other_speeches = "\n".join([f"玩家{player_id}】发言：{speech}" for player_id, speech in player_speeches.items()])
            prompt = manager.get_player_speech_prompt(player, other_speeches, state["current_round"])
            # response = llm.invoke(prompt)
            speech: str = ""
            print(f"玩家({player.id}){player.name}】发言：")
            for chunk in llm.stream(prompt):
                speech += chunk.text
                print(chunk.text, end="", flush=True)
            print()  # 结束换行
            player_speeches[player.id] = speech
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
        print(f"玩家【{player.name}】投票中")
        # 人类玩家投票
        if player.player_type == PlayerType.HUMAN:
            print(f"玩家【{player.name}】您想投票给谁？目前场上仍存活的玩家有：\n")
            for player_id in alive_players:
                print(f"玩家【{player_id}】")
            vote_for_id = int(input("请输入玩家编号 > "))
        else:
            # AI玩家投票
            prompt = manager.get_player_vote_prompt(
                player, state["round_speech"], alive_players
            )
            response = llm.invoke(prompt)
            vote_for_id = int(str(response.content))
            # print(f"{player.name} 的投票结果是 {vote_for_id}")
        player_votes[player.id] = vote_for_id

    # 更新状态
    state["round_votes"] = player_votes
    return state

def process_elimination_node(state: GameState) -> GameState:
    """处理淘汰结果"""
    all_players = state["players"]
    votes = state["round_votes"]
    print("\n【本回合投票结果】\n")

    for player_id, vote_for_id in votes.items():
        player = next(player for player in all_players if player.id == player_id)
        vote_for_player = next(player for player in all_players if player.id == vote_for_id)
        print(f"玩家({player_id})【{player.name}】的投票结果是【{vote_for_player.name}】")

    # 统计票数 {user_id: vote_count}
    vote_count: dict[int, int] = {}
    for vote_for_id in votes.values():
        vote_count[vote_for_id] = vote_count.get(vote_for_id, 0) + 1

    print("\n正在归票...\n")
    # 展示投票结果
    # TODO 考虑平票的case
    for player_id, count in vote_count.items():
        name = next(player.name for player in all_players if player.id == player_id)
        print(f"玩家({player_id})【{name}】】获得{count}票")

    # 找出得票最高的玩家
    eliminated_id = max(vote_count, key=vote_count.get)
    eliminated_player = next(player for player in all_players if player.id == eliminated_id)

    # 淘汰玩家
    eliminated_player.is_alive = False
    state["eliminated_players"].append(eliminated_id)

    # 显示被淘汰玩家的信息
    role_display = "【卧底】💣" if eliminated_player.player_role == PlayerRole.UNDERCOVER else "【普通玩家】"
    print(f"被淘汰的玩家是【{eliminated_player.name}】，其身份是{role_display}，词语是【{eliminated_player.word}】")

    # 记录到历史
    state["game_history"].append({
        "round": state["current_round"],
        "eliminated_id": eliminated_id,
        "eliminated_name": eliminated_player.name,
        "eliminated_role": eliminated_player.player_role.value,
        "votes": state["round_votes"].copy(),
        "speeches": state["round_speech"].copy(),
    })
    return state


def check_game_end_node(state: GameState):
    """检查游戏是否结束"""
    # 卧底淘汰，平民获胜
    # 卧底和平民数量一致，卧底获胜
    # 否则，游戏继续
    alive_players: list[Player] = [p for p in state["players"] if p.is_alive]
    alive_undercover: list[Player] = [p for p in alive_players if p.player_role == PlayerRole.UNDERCOVER]

    # 判定游戏结束条件
    # 1. 卧底淘汰，平民获胜
    if len(alive_undercover) == 0:
        print("\n🎉 游戏结束！普通玩家获胜！卧底已被淘汰。")
        state["game_history"].append({
            "game_end": "普通玩家获胜",
            "rounds": state["current_round"],
        })
    elif len(alive_players) <= 2:
        # 场上还有2个，且卧底存活，卧底胜利
        print("\n🎉 游戏结束！卧底获胜！")
        state["game_history"].append({
            "game_end": "卧底玩家获胜",
            "rounds": state["current_round"],
        })
    else:
        # 游戏继续
        state["current_round"] += 1
        state["game_status"] = GameStatus.ROUND_RESULT
        return state

    return state


def game_end_node(state: GameState) -> GameState:
    """游戏结束节点"""
    print("=" * 60)
    print("游戏结束！")
    print("=" * 60)

    for player in state["players"]:
        # 角色翻译
        role_display = "【卧底】💣" if player.player_role == PlayerRole.UNDERCOVER else "【平民】"
        print(f"玩家【{player.id}】{player.name}】的身份是{role_display}，词语是【{player.word}】")
    state["game_status"] = GameStatus.GAME_END
    return state