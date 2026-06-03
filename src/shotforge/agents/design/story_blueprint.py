from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StoryBeat:
    description: str
    emotional_goal: str
    key_visuals: list[str]
    shot_type: str
    camera: str
    subject_motion: str
    transition: str
    pacing: str
    music: str
    sound_design: list[str]
    action_upgrade: str
    emotion_upgrade: str
    scene_upgrade: str
    camera_upgrade: str
    audio_upgrade: str


def build_story_beats(
    *,
    idea: str,
    language: str,
    required_elements: list[str],
    count: int,
) -> list[StoryBeat]:
    lowered = idea.lower()
    if _is_elevator_revenge(lowered):
        beats = _elevator_revenge_beats(language)
    else:
        beats = _generic_beats(idea, language, required_elements)
    while len(beats) < count:
        beats.append(_generic_followup_beat(idea, language, len(beats) + 1, required_elements))
    return beats[:count]


def _is_elevator_revenge(lowered: str) -> bool:
    has_revenge = "revenge" in lowered or "复仇" in lowered
    has_elevator = "elevator" in lowered or "电梯" in lowered
    return has_revenge and has_elevator


def _elevator_revenge_beats(language: str) -> list[StoryBeat]:
    if language == "zh":
        return [
            StoryBeat(
                description=(
                    "深色西装的女高管独自走进镜面豪华电梯，雨水从伞尖滴到大理石地面。"
                    "她把一张黑色门禁卡藏在掌心，电梯门即将合上时，曾经背叛她的合伙人挤进来。"
                ),
                emotional_goal="压抑、克制，观众感觉她已经准备好反击。",
                key_visuals=["镜面电梯", "黑色门禁卡", "雨水伞尖", "前合伙人"],
                shot_type="wide establishing",
                camera="low wide shot reflected in elevator mirrors",
                subject_motion="she steps in, hides the access card, and never looks directly at him",
                transition="doors close into a hard cut",
                pacing="slow controlled setup with one precise prop reveal",
                music="low pulse under elevator hum",
                sound_design=["rain drip on marble", "soft elevator chime", "doors sealing shut"],
                action_upgrade="Show her thumb sliding the black card into view before the doors close.",
                emotion_upgrade="Hold on her still face while his reflection shows unease behind her.",
                scene_upgrade="Keep the mirror seams, brass trim, floor display, and rain droplets visible.",
                camera_upgrade="Use the mirror reflection to frame both characters without cutting away.",
                audio_upgrade="Let the door seal mute the outside rain and isolate the two characters.",
            ),
            StoryBeat(
                description=(
                    "她轻轻把黑色门禁卡贴上隐藏扫描器，电梯楼层从 12 跳到私人楼层 88。"
                    "合伙人低头时，在她手提箱的反光金属牌上看见自己偷走的原型机标志。"
                ),
                emotional_goal="紧张升级，复仇证据第一次变得可见。",
                key_visuals=["隐藏扫描器", "楼层 12 到 88", "原型机标志", "金属手提箱"],
                shot_type="tracking medium",
                camera="tight tracking shot from access card to floor indicator to reflected briefcase logo",
                subject_motion="she taps the scanner, lets the floor number jump, and tilts the briefcase into his sightline",
                transition="floor display flash cut",
                pacing="three readable beats: card tap, floor jump, reflected logo",
                music="pulse tightens with a metallic tick",
                sound_design=["scanner beep", "floor indicator jump", "briefcase latch click"],
                action_upgrade="Make the card tap, floor jump, and briefcase reveal happen as three separate visible actions.",
                emotion_upgrade="Cut to his eyes recognizing the logo, then back to her calm half-smile.",
                scene_upgrade="Place the hidden scanner under the brass rail so the action has a clear target.",
                camera_upgrade="Rack focus from her hand to the number 88, then to his reflected face.",
                audio_upgrade="Sync the scanner beep with the floor display jump.",
            ),
            StoryBeat(
                description=(
                    "电梯灯短暂熄灭又亮起，墙面屏幕播放一段监控视频：他把公司密钥交给竞争对手。"
                    "她终于抬眼，电梯镜面把她和证据屏幕叠在同一画面里。"
                ),
                emotional_goal="反转揭示，安静的复仇从暗示变成实锤。",
                key_visuals=["监控视频", "公司密钥", "竞争对手", "镜面叠影"],
                shot_type="dynamic close-up",
                camera="slow orbit close-up that keeps her eyes, his reflection, and the evidence screen aligned",
                subject_motion="she raises her eyes as the evidence screen lights up and he freezes mid-breath",
                transition="blackout blink into evidence screen",
                pacing="brief blackout, evidence flash, silent recognition",
                music="sub-bass drop under a thin glass tone",
                sound_design=["lights flicker", "screen turns on", "his breath stops"],
                action_upgrade="Make the reveal object explicit: the wall screen shows the stolen key handoff.",
                emotion_upgrade="Hold the silence after he recognizes the evidence instead of adding dialogue.",
                scene_upgrade="Anchor the proof on the elevator wall screen, not as abstract backstory.",
                camera_upgrade="Keep the evidence screen readable while her face remains dominant.",
                audio_upgrade="Drop the music for half a second when the evidence appears.",
            ),
            StoryBeat(
                description=(
                    "电梯到达 88 层，门开向一间空旷董事会会议室，所有座位前都亮着同一份证据文件。"
                    "她走出去，把门禁卡留在地上；门合上时，他被留在电梯里，楼层开始倒数。"
                ),
                emotional_goal="冷静收束，复仇完成但不需要大声宣告。",
                key_visuals=["88 层会议室", "亮起的证据文件", "落地门禁卡", "倒数楼层"],
                shot_type="hero wide",
                camera="wide pullback from opening doors to the empty boardroom table",
                subject_motion="she exits without turning back, drops the card, and leaves him trapped in the closing reflection",
                transition="doors close on his reflection",
                pacing="clean release: doors open, proof revealed, card dropped, doors close",
                music="low pulse resolves into a cold sustained note",
                sound_design=["doors opening", "card hitting marble", "floor counter ticking down"],
                action_upgrade="End with the card hitting the floor and the counter starting its countdown.",
                emotion_upgrade="Keep her exit calm; the revenge lands through the room full of evidence.",
                scene_upgrade="Show every boardroom monitor carrying the same proof file.",
                camera_upgrade="Pull back wide enough to reveal the boardroom before the doors close.",
                audio_upgrade="Use the falling card as the final audible punctuation.",
            ),
        ]
    return [
        StoryBeat(
            description=(
                "A woman in a dark tailored suit enters a mirrored luxury elevator, rain dripping "
                "from the tip of her umbrella. She hides a black access card in her palm as the "
                "former partner who betrayed her slips in before the doors close."
            ),
            emotional_goal="Controlled tension; the audience senses she has prepared the counterattack.",
            key_visuals=["mirrored elevator", "black access card", "rain on umbrella tip", "former partner"],
            shot_type="wide establishing",
            camera="low wide shot reflected in elevator mirrors",
            subject_motion="she steps in, hides the access card, and never looks directly at him",
            transition="doors close into a hard cut",
            pacing="slow controlled setup with one precise prop reveal",
            music="low pulse under elevator hum",
            sound_design=["rain drip on marble", "soft elevator chime", "doors sealing shut"],
            action_upgrade="Show her thumb sliding the black card into view before the doors close.",
            emotion_upgrade="Hold on her still face while his reflection shows unease behind her.",
            scene_upgrade="Keep the mirror seams, brass trim, floor display, and rain droplets visible.",
            camera_upgrade="Use the mirror reflection to frame both characters without cutting away.",
            audio_upgrade="Let the door seal mute the outside rain and isolate the two characters.",
        ),
        StoryBeat(
            description=(
                "She lightly taps the black access card against a hidden scanner. The floor display "
                "jumps from 12 to private floor 88. As he looks down, the mirrored metal tag on her "
                "briefcase reveals the logo of the prototype he stole."
            ),
            emotional_goal="Escalating tension; the revenge evidence becomes visible for the first time.",
            key_visuals=["hidden scanner", "floor 12 to 88", "prototype logo", "metal briefcase"],
            shot_type="tracking medium",
            camera="tight tracking shot from access card to floor indicator to reflected briefcase logo",
            subject_motion="she taps the scanner, lets the floor number jump, and tilts the briefcase into his sightline",
            transition="floor display flash cut",
            pacing="three readable beats: card tap, floor jump, reflected logo",
            music="pulse tightens with a metallic tick",
            sound_design=["scanner beep", "floor indicator jump", "briefcase latch click"],
            action_upgrade="Make the card tap, floor jump, and briefcase reveal happen as three separate visible actions.",
            emotion_upgrade="Cut to his eyes recognizing the logo, then back to her calm half-smile.",
            scene_upgrade="Place the hidden scanner under the brass rail so the action has a clear target.",
            camera_upgrade="Rack focus from her hand to the number 88, then to his reflected face.",
            audio_upgrade="Sync the scanner beep with the floor display jump.",
        ),
        StoryBeat(
            description=(
                "The elevator lights blink off and return. A wall screen plays security footage of "
                "him handing the company's encryption key to a competitor. She finally raises her "
                "eyes, with her face and the evidence screen layered in the mirror."
            ),
            emotional_goal="The reversal becomes undeniable proof rather than vague accusation.",
            key_visuals=["security footage", "company encryption key", "competitor", "mirror overlay"],
            shot_type="dynamic close-up",
            camera="slow orbit close-up that keeps her eyes, his reflection, and the evidence screen aligned",
            subject_motion="she raises her eyes as the evidence screen lights up and he freezes mid-breath",
            transition="blackout blink into evidence screen",
            pacing="brief blackout, evidence flash, silent recognition",
            music="sub-bass drop under a thin glass tone",
            sound_design=["lights flicker", "screen turns on", "his breath stops"],
            action_upgrade="Make the reveal object explicit: the wall screen shows the stolen key handoff.",
            emotion_upgrade="Hold the silence after he recognizes the evidence instead of adding dialogue.",
            scene_upgrade="Anchor the proof on the elevator wall screen, not as abstract backstory.",
            camera_upgrade="Keep the evidence screen readable while her face remains dominant.",
            audio_upgrade="Drop the music for half a second when the evidence appears.",
        ),
        StoryBeat(
            description=(
                "The elevator opens onto an empty boardroom on floor 88, every seat lit by the same "
                "evidence file. She walks out and drops the access card on the marble. As the doors "
                "close, he remains trapped inside and the floor counter begins to count down."
            ),
            emotional_goal="Cold resolution; the revenge lands through evidence and control, not shouting.",
            key_visuals=["floor 88 boardroom", "evidence files", "dropped access card", "countdown display"],
            shot_type="hero wide",
            camera="wide pullback from opening doors to the empty boardroom table",
            subject_motion="she exits without turning back, drops the card, and leaves him trapped in the closing reflection",
            transition="doors close on his reflection",
            pacing="clean release: doors open, proof revealed, card dropped, doors close",
            music="low pulse resolves into a cold sustained note",
            sound_design=["doors opening", "card hitting marble", "floor counter ticking down"],
            action_upgrade="End with the card hitting the floor and the counter starting its countdown.",
            emotion_upgrade="Keep her exit calm; the revenge lands through the room full of evidence.",
            scene_upgrade="Show every boardroom monitor carrying the same proof file.",
            camera_upgrade="Pull back wide enough to reveal the boardroom before the doors close.",
            audio_upgrade="Use the falling card as the final audible punctuation.",
        ),
    ]


def _generic_beats(idea: str, language: str, required_elements: list[str]) -> list[StoryBeat]:
    anchor = _anchor_text(required_elements)
    if language == "zh":
        return [
            _generic_zh(idea, anchor, 1, "用一个清晰主体和一个可见道具建立目标。"),
            _generic_zh(idea, anchor, 2, "让主体对道具采取一次可观察动作，并出现明确结果。"),
            _generic_zh(idea, anchor, 3, "揭示新的信息锚点，让观众理解局势发生变化。"),
            _generic_zh(idea, anchor, 4, "用最终动作和环境变化完成收束。"),
        ]
    return [
        _generic_en(idea, anchor, 1, "establish the subject, the setting, and one visible prop goal"),
        _generic_en(idea, anchor, 2, "make the subject take one observable action with a clear result"),
        _generic_en(idea, anchor, 3, "reveal a new information anchor that changes the audience reading"),
        _generic_en(idea, anchor, 4, "resolve the beat with one final action and a changed environment"),
    ]


def _generic_followup_beat(
    idea: str,
    language: str,
    index: int,
    required_elements: list[str],
) -> StoryBeat:
    anchor = _anchor_text(required_elements)
    if language == "zh":
        return _generic_zh(idea, anchor, index, "补充一个新的视觉证据点，推动任务进入下一阶段。")
    return _generic_en(idea, anchor, index, "add a new visual proof point and move the task forward")


def _generic_en(idea: str, anchor: str, index: int, action: str) -> StoryBeat:
    return StoryBeat(
        description=(
            f"Beat {index}: {idea}. The frame must {action}. Keep {anchor} visible as concrete "
            "foreground or midground anchors instead of vague background texture."
        ),
        emotional_goal="Make the story change legible through visible action and reaction.",
        key_visuals=[anchor, "foreground prop", "visible reaction", "stable location"],
        shot_type=["wide establishing", "tracking medium", "dynamic close-up", "hero wide"][
            (index - 1) % 4
        ],
        camera=["wide lock-off", "side tracking", "slow push-in", "crane pullback"][(index - 1) % 4],
        subject_motion="start pose -> one concrete action -> visible reaction or outcome",
        transition=["hard cut", "match cut", "blink cut", "clean hold"][(index - 1) % 4],
        pacing="one readable action beat before the next cut",
        music="controlled cinematic pulse",
        sound_design=["single prop sound", "room tone shift", "clear transition hit"],
        action_upgrade="Replace abstract movement with one named verb, one target object, and one outcome.",
        emotion_upgrade="Add a visible reaction on the face, hands, or posture after the action lands.",
        scene_upgrade="Name the location anchor and keep it visible across the shot.",
        camera_upgrade="Frame the action target and the reaction in the same shot whenever possible.",
        audio_upgrade="Place a sound cue exactly on the action outcome.",
    )


def _generic_zh(idea: str, anchor: str, index: int, action: str) -> StoryBeat:
    return StoryBeat(
        description=(
            f"第 {index} 段：{idea}。画面需要{action}保持 {anchor} 作为前景或中景中的具体锚点，"
            "不要只做成模糊背景氛围。"
        ),
        emotional_goal="通过可见动作和反应，让故事变化被观众看懂。",
        key_visuals=[anchor, "前景道具", "可见反应", "稳定地点"],
        shot_type=["wide establishing", "tracking medium", "dynamic close-up", "hero wide"][
            (index - 1) % 4
        ],
        camera=["wide lock-off", "side tracking", "slow push-in", "crane pullback"][(index - 1) % 4],
        subject_motion="起始姿态 -> 一个具体动作 -> 可见反应或结果",
        transition=["hard cut", "match cut", "blink cut", "clean hold"][(index - 1) % 4],
        pacing="剪切前保留一个可读动作节拍",
        music="克制的电影感脉冲",
        sound_design=["单一道具声", "空间底噪变化", "清晰转场点"],
        action_upgrade="把抽象运动替换为一个明确动词、一个目标物和一个结果。",
        emotion_upgrade="在动作落点后增加脸、手或姿态上的可见反应。",
        scene_upgrade="明确地点锚点，并在整个镜头中保持可见。",
        camera_upgrade="尽量在同一个镜头里同时框住动作目标和反应。",
        audio_upgrade="把声音点位对齐到动作结果上。",
    )


def _anchor_text(required_elements: list[str]) -> str:
    if required_elements:
        return ", ".join(required_elements[:4])
    return "the primary subject, key prop, and location"
