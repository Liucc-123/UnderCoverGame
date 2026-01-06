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
    GAME_END = "game_end"  # 游戏结束


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
    player_role: PlayerRole = None
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


class UnderCoverGameManager:
    """谁是卧底游戏管理器"""

    def __init__(self):
        """初始化方法"""
        # 初始化实例时，将传入的llm参数赋值给实例的llm属性
        self.llm = llm

    def initialize_game(self) -> GameState:
        """初始化游戏"""
        # 创建玩家
        players: list[Player] = [
            Player(id=0, name="人类", player_type=PlayerType.HUMAN),
            Player(id=1, name="AI1", player_type=PlayerType.AI),
            Player(id=2, name="AI2", player_type=PlayerType.AI),
            Player(id=3, name="AI3", player_type=PlayerType.AI),
        ]

        # 随机打乱玩家顺序
        random.shuffle(players)
        # 重新分配ID
        for i, player in enumerate(players):
            player.id = i

        # 随机选择一个卧底
        undercover_id = random.randint(0, 3)
        normal_word, undercover_word = random.choice(WORD_PAIRS)

        # 分配角色和词语
        for player in players:
            if player.id == undercover_id:
                player.player_role = PlayerRole.UNDERCOVER
                player.word = undercover_word
            else:
                player.player_role = PlayerRole.NORMAL
                player.word = normal_word

        # 人类玩家
        player = next(player for player in players if player.player_type == PlayerType.HUMAN)
        print(f"你看到的词语是: {player.word}")

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

    def get_player_speech_prompt(self, player: Player, other_speeches: str, game_round: int) -> str:
        """获取AI玩家发言的提示词"""
        # 获取玩家身份
        role = "平民" if player.player_role == PlayerRole.NORMAL else "卧底"
        # 给AI玩家生成发言
        return dedent(f"""
        你正在玩"谁是卧底"游戏，结合游戏规则、你拿到的【词语】和【其他玩家的发言】进行发言。
        你并不知道你的身份，根据自己的【词语】和【其他玩家的发言】来猜测自己的身份。
        
        ---
        【要求】
        - 禁止在发言中直接表明你的身份，如"我是卧底..."
        - 禁止在发言中直接说出词语本身或提到相关字眼，如词语是"棉花糖"，发言中不能出现"棉花糖"字眼
        - 如果你是【平民】，在描述自己的词语时，避免过于直接，防止被【卧底】直接猜出平民词语；
        - 如果你是【卧底】，*想办法存活下来*，如通过其他平民玩家的发言猜出他们的词语，根据所猜想的词语进行发言，以此来干扰场上信息，避免被其他玩家把自己投出去
        ---
        【现在的游戏轮数】
        现在游戏进行到第{game_round}轮！
        ---
        【游戏技巧】
        限制：只表达词语的一两个方面，字数在10个左右。
        示例：你拿到的词语是：公路
        第1-2轮可以这样描述："我的词语和交通有关"
        第3轮及以后可以这样描述：常见于城镇之间的长距离路段，路面平整、车道明确，两侧常有护栏和交通标志，沿线会有服务区或收费站，主要供机动车长途行驶和货物运输
        ---
        【词语】
        {player.word}
        ---
        【其他玩家的发言】
        {other_speeches}
        ---
        你的发言：
        """)

    def get_player_vote_prompt(self, player: Player, other_speeches: dict[int, str], alive_players: list[int]):
        """获取AI玩家投票的提示词"""
        # 获取玩家身份
        role = "平民" if player.player_role == PlayerRole.NORMAL else "卧底"

        # 其他玩家发言
        speeches = "\n".join([f"玩家{player_id}的发言：{other_speeches[player_id]}" for player_id in alive_players if
                              player_id != player.id])

        return dedent(f"""
        结合"谁是卧底"的游戏规则、你自己的【身份词】、你拿到的【词语】及【其他存活玩家的发言】对你认为身份可疑的玩家进行投票（玩家编号）。
        - 你是卧底，投票给其他存活玩家
        - 你是平民，投票给身份可疑的玩家
        ---
        【身份词】
        {role}
        ---
        【你的词语】
        {player.word}
        ---
        【其他存活玩家的发言】
        {speeches}
        ---
        请直接输出你要投票的玩家编号，不要输出其他多余内容：
        """)