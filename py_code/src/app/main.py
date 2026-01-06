"""
File: main.py
Created Time: 2026-01-06
Author: falcon (liuc47810@gmail.com)
"""
from src.graph.types import UnderCoverGameManager
from src.graph.builder import build_game_graph

# ==================== 游戏主入口 ====================
def play_game():
    """主游戏函数"""
    print("🐱 欢迎来到【谁是卧底】游戏！")
    print("-" * 60)
    print("游戏规则：")
    print("1. 4名玩家，其中1名是卧底")
    print("2. 卧底看到的词与其他玩家不同")
    print("3. 每一轮，每个玩家用一句话描述自己的词（不能直接说出来）")
    print("4. 然后所有玩家投票淘汰可疑的玩家")
    print("5. 如果卧底被淘汰，普通玩家获胜；否则卧底获胜")
    print("=" * 60)

    # 初始化游戏
    manager = UnderCoverGameManager()
    initial_state = manager.initialize_game()

    # 构建和执行游戏流程
    game_graph = build_game_graph()

    # 进行游戏
    game_graph.invoke(initial_state)

    print("\n✨ 感谢游玩！")
# 导出 game_graph 供 langgraph 使用
game_graph = build_game_graph()

if __name__ == "__main__":
    play_game()
