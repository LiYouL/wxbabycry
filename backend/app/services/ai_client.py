# backend/app/services/ai_client.py
import asyncio
from typing import Optional

from anthropic import AsyncAnthropic
from app.config import settings
from app.schemas.cry import CryAdvice

SYSTEM_PROMPT = """你是一位经验丰富的育儿专家，擅长帮助新手父母理解婴儿的需求。

根据哭声识别结果，你需要：
1. 用温暖亲切的语气解释婴儿可能的状况
2. 提供具体可操作的解决方案
3. 给出安抚建议
4. 必要时提醒家长关注其他症状

请用中文回复。"""


def build_prompt(cry_type: str, confidence: float, baby_info: Optional[dict]) -> str:
    info_parts = [f"哭声识别结果：{cry_type}（置信度 {confidence:.0%}）"]

    if baby_info:
        if baby_info.get("nickname"):
            info_parts.append(f"宝宝昵称：{baby_info['nickname']}")
        if baby_info.get("feed_type"):
            info_parts.append(f"喂养方式：{baby_info['feed_type']}")
        if baby_info.get("birthday"):
            info_parts.append(f"出生日期：{baby_info['birthday']}")

    context = "\n".join(info_parts)

    return f"""请根据以下信息提供育儿建议：

{context}

请按以下格式回复（严格 JSON 格式）：
{{
  "cause": "哭声原因解释（1-2句）",
  "solutions": ["解决方案1", "解决方案2"],
  "soothing_tips": ["安抚技巧1", "安抚技巧2"],
  "warnings": ["注意事项（如需要）"]
}}"""


async def generate_advice(
    cry_type: str, confidence: float, baby_info: Optional[dict] = None
) -> CryAdvice:
    if not settings.enable_ai_advice or not settings.anthropic_api_key:
        return _fallback_advice(cry_type)

    prompt = build_prompt(cry_type, confidence, baby_info)

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    try:
        response = await asyncio.wait_for(
            client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=512,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            ),
            timeout=3.0,
        )
        import json

        text = response.content[0].text
        data = json.loads(text)
        return CryAdvice(**data)
    except Exception:
        return _fallback_advice(cry_type)


def _fallback_advice(cry_type: str) -> CryAdvice:
    fallbacks = {
        "饥饿": CryAdvice(
            cause="宝宝可能因为饥饿而哭闹",
            solutions=["尝试给宝宝喂奶", "观察宝宝是否有觅食反射（转头、张嘴）"],
            soothing_tips=["喂奶时保持安静环境", "喂完后轻拍背部帮助排气"],
            warnings=["如持续拒绝进食，请咨询医生"],
        ),
        "尿布不适": CryAdvice(
            cause="宝宝可能因为尿布湿了或不舒适而哭闹",
            solutions=["检查并及时更换尿布", "清洁并保持臀部干燥"],
            soothing_tips=["更换尿布时用温水清洗", "涂抹护臀霜预防红臀"],
            warnings=["如出现严重红疹请就医"],
        ),
        "疲倦": CryAdvice(
            cause="宝宝可能感到疲倦，需要睡觉",
            solutions=["创造一个安静、昏暗的睡眠环境", "尝试包裹襁褓增加安全感"],
            soothing_tips=["播放白噪音帮助入睡", "轻轻摇晃或轻拍宝宝"],
            warnings=["如长时间无法入睡，请观察是否有其他不适"],
        ),
        "疼痛": CryAdvice(
            cause="宝宝可能因腹痛、胀气等不适而哭闹",
            solutions=["检查宝宝腹部是否胀硬", "尝试顺时针轻揉宝宝腹部"],
            soothing_tips=["飞机抱姿势可缓解胀气", "温水浴可帮助放松"],
            warnings=["如持续哭闹超过30分钟，建议及时就医"],
        ),
        "需要安抚": CryAdvice(
            cause="宝宝需要安抚和关注，可能感到孤单或不安",
            solutions=["抱起宝宝轻轻安抚", "对宝宝说话或唱歌"],
            soothing_tips=["用温柔的声音和宝宝交流", "轻轻抚摸宝宝的背部"],
            warnings=["观察宝宝是否有其他不适症状，不要长时间让宝宝独自哭闹"],
        ),
        "其他": CryAdvice(
            cause="宝宝的哭声原因不太明确",
            solutions=["逐一检查：是否饿了、尿布湿了、困了、太热/太冷"],
            soothing_tips=["抱抱宝宝，让宝宝感受到安全感", "带宝宝到不同环境走走"],
            warnings=["如果宝宝持续哭闹且无法安抚，建议咨询儿科医生"],
        ),
    }
    return fallbacks.get(cry_type, fallbacks["其他"])
