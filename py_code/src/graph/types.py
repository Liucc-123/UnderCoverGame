"""
File: types.py
Created Time: 2026-01-05
Author: falcon (liuc47810@gmail.com)
"""

from typing import TypedDict, Annotated
from enum import Enum
from dataclasses import dataclass
from langgraph.graph.message import add_messages
from src.agents.llm import llm
from src.constants.words import WORD_PAIRS
from src.prompts.prompt import GAME_CONTEXT
from textwrap import dedent

import random


class GameStatus(Enum):
    """游戏状态"""

    INIT = "init"  # 初始状态
    ROUND_SPEECH = "round_speech"  # 发言阶段
    ROUND_VOTING = "round_voting"  # 投票阶段
    ROUND_RESULT = "round_result"  # 回合结果
    GAME_END = "game_end"  #  游戏结束


class PlayerRole(Enum):
    """玩家角色"""

    NORMAL = "normal"  # 普通玩家
    UNDERCOVER = "undercover"  # 卧底


class PlayerType(Enum):
    """玩家类型"""

    HUMAN = "human"  # 人类玩家
    AI = "ai"  # AI玩家


@dataclass
class Player:
    """玩家信息"""

    id: int
    name: str
    player_type: PlayerType
    player_role: PlayerRole
    word: str = ""  # 玩家看到的词
    is_alive: bool = True  # 玩家当前是否存活
    speech: str = ""  # 玩家当前回合的发言
    votes_received: int = 0  # 当前回合获得的投票数
    vote_for: int = -1  # 投给谁（玩家ID）

    def reset_round(self):
        """重置玩家回合数据"""

        self.speech = ""
        self.votes_received = 0
        self.vote_for = -1


class GameState(TypedDict):
    """游戏状态"""

    game_status: GameStatus
    players: list[Player]
    current_round: int
    round_speech: dict[int, str]  # 玩家发言 {player_id: speech}
    round_votes: dict[int, int]  # 玩家投票记录 {player_id: vote_for_id}
    game_history: list[dict]  # 游戏历史记录
    eliminated_players: list[int]  # 淘汰的玩家id列表
    messages: Annotated[list, add_messages]


# ==================== 游戏管理器 ====================
class UnderCoverGameManager:
    """谁是卧底游戏管理器"""

    def __init__(self):
        """
        初始化方法
        初始化实例时，将传入的llm参数赋值给实例的llm属性
        """
        self.llm = llm  # 将传入的llm参数赋值给实例的llm属性

    def initialize_game(self) -> GameState:
        """初始化游戏"""

        # 创建玩家
        players: list[Player] = [
            Player(id=0, name="玩家（你）", player_type=PlayerType.HUMAN),
            Player(id=1, name="AI1", player_type=PlayerType.AI),
            Player(id=2, name="AI2", player_type=PlayerType.AI),
            Player(id=3, name="AI3", player_type=PlayerType.AI),
        ]
        # 随机选择一个卧底
        undercover_id = random.randint(0, 3)
        normal_word, undercover_word = random.choice(WORD_PAIRS)

        # 分配角色和词语
        for player in players:
            if player.id == undercover_id:
                player.player_role = PlayerRole.UNDERCOVER
                player.word = normal_word
            else:
                player.player_role = PlayerRole.NORMAL
                player.word = undercover_word

        # 如果人类玩家是卧底，需告知
        if undercover_id == 0:
            print("\n🎮 游戏开始！你是 【卧底】！")
            word = undercover_word
        else:
            print("\n🎮 游戏开始！")
            word = normal_word
            print(f"【卧底在其他三名AI玩家中】")
        print(f"你看到的词语是：{word}")

        # 返回初始游戏状态
        return GameState(
            game_status=GameStatus.INIT,
            players=players,
            current_round=1,
            round_speech={},
            round_votes={},
            game_history=[],
            eliminated_players=[],
            messages=[],
        )

    def get_player_speech_prompt(player: Player) -> str:
        """获取AI玩家发言的提示词"""

        # 获取玩家身份
        role = "平民" if player.player_role == PlayerRole.NORMAL else "卧底"
        """给AI玩家生成发言"""
        return dedent(
            f"""
        你正在玩“谁是卧底”游戏。结合【游戏规则】和你的【身份词】进行发言。
        
        ---
        【游戏规则】
        {GAME_CONTEXT}
        ---
        【身份词】
        {role}
        ---
        """
        )
    
    def get_player_vote_prompt(player: Player, other_speeches: dict[int, str], alive_players: list[int]):
        """获取AI玩家投票的提示词"""
        # 获取玩家身份
        role = "平民" if player.player_role == PlayerRole.NORMAL else "卧底"
        
        # 其他玩家发言
        speeches = "\n".join(f"玩家{player_id} 的发言: {other_speeches[player_id]}" for player_id in alive_players)
        
        return dedent(f"""
        结合“谁是卧底”的【游戏规则】、你自己的【身份词】及【其他存活玩家的发言】对你认为身份可疑的玩家进行投票（玩家编号）。
        
        ---
        【游戏规则】
        {GAME_CONTEXT}
        ---
        【身份词】
        {role}
        ---
        【其他存活玩家的发言】
        {speeches}
        ---
        【要求】
        只给出投票结果，禁止任何其他解释。
        示例输出：1
        ---
        """)
        