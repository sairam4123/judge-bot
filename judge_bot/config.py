from dataclasses import dataclass


@dataclass
class JudgeBotConfig:
    model: str = "gemini-2.5-flash-lite"
