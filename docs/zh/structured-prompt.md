# ShotForge / 镜铸 — 结构化 PromptTemplate 设计

> 创建日期：2026-05-27 | 状态：设计阶段

---

## 🎯 为什么需要结构化 Prompt

```
旧版：一整段 prompt 文本 → 评测说"不好" → 不知道怎么改
新版：12 个独立字段 → 评测定位到"action_sequence 太抽象" → 定向改该字段
```

**核心价值：** 评测结果可以精准回写到具体字段，不会把已经好的部分改坏。

---

## 📐 PromptTemplate 12 字段

```python
from pydantic import BaseModel, Field

class PromptTemplate(BaseModel):
    # ── L1: 硬目标（V1 评测用）──
    factual_constraints: str = ""
    """事实性约束：桌子上有一个红苹果，背景是雨夜上海弄堂"""
    
    character_identity: str = ""
    """角色身份：女性, 30岁, 红风衣, 短发"""
    
    scene_constraints: str = ""
    """场景约束：雨夜, 上海弄堂门口, 霓虹灯招牌"""
    
    object_constraints: str = ""
    """关键道具：左手的录音笔, 右手的手机"""
    
    action_sequence: str = ""
    """动作序列：拿起手机 → 播放录音 → 对方表情变化 → 后退半步"""
    
    # ── L2: 运动与时序（V2 评测用）──
    motion_direction: str = ""
    """运动方向：缓慢推近, 手持微晃, 跟随主体右移"""
    
    # ── L3: 风格与画面（V3 评测用）──
    camera_direction: str = ""
    """镜头语言：中景, 低角度, 浅景深, 霓虹灯光晕"""
    
    style_direction: str = ""
    """风格方向：赛博朋克, 电影感, 低饱和, 高对比"""
    
    # ── L4: 情绪表达（V4 评测用）──
    emotional_direction: str = ""
    """情绪方向：由冷静转为愤怒, 对方由轻蔑转为慌张"""
    
    # ── L5: 叙事控制（V5 评测用）──
    narrative_beat: str = ""
    """叙事节拍：录音播放的瞬间是反转点, 情绪在此刻爆发"""
    
    # ── 负向约束 ──
    negative_prompt: str = ""
    """负面提示词：模糊, 变形, 多余肢体, 文字乱码"""
    
    # ── 生成参数 ──
    comfyui_params: dict = Field(default_factory=lambda: {
        "seed": -1,
        "steps": 30,
        "cfg": 7.0,
        "width": 512,
        "height": 512,
    })
    """ComfyUI 特定参数"""
```

---

## 🔗 字段与评测维度的映射

| PromptTemplate 字段 | V1 评测维度 | V2+ 评测维度 |
|---------------------|-----------|------------|
| `factual_constraints` | 主体存在性 | — |
| `character_identity` | 主体存在性、主体数量 | 角色一致性 (V4) |
| `scene_constraints` | 场景匹配 | 场景一致性 (V3) |
| `object_constraints` | 关键道具 | — |
| `action_sequence` | 动作发生 | 运动连贯性 (V2) |
| `motion_direction` | — | 运动方向 (V2) |
| `camera_direction` | — | 镜头语言 (V3) |
| `style_direction` | — | 风格匹配 (V3) |
| `emotional_direction` | — | 情绪表达 (V4) |
| `narrative_beat` | — | 叙事控制 (V5) |
| `negative_prompt` | 全局排除 | 全局排除 |
| `comfyui_params` | — | 参数调优 |

---

## 🎨 从结构化 Prompt 到 ComfyUI 工作流

```python
def template_to_workflow_json(template: PromptTemplate) -> dict:
    """将 PromptTemplate 转为 ComfyUI API 可用的 workflow JSON"""
    return {
        "positive_prompt": _join_nonempty([
            template.factual_constraints,
            template.character_identity,
            template.scene_constraints,
            template.object_constraints,
            template.action_sequence,
            template.motion_direction,
            template.camera_direction,
            template.style_direction,
            template.emotional_direction,
            template.narrative_beat,
        ]),
        "negative_prompt": template.negative_prompt,
        "seed": template.comfyui_params["seed"],
        "steps": template.comfyui_params["steps"],
        "cfg": template.comfyui_params["cfg"],
    }
```

**设计原则：** 所有非空字段用逗号连接——这样评测如果发现"风格不对"，可以直接修改 `style_direction` 字段，不动其他部分。

---

## 🔧 评测结果如何回写

```
例子：
  评测发现 action_sequence 导致"动作不连贯"

修改前：
  action_sequence: "拿起手机播放录音对方表情变化"
  
修改后（RedesignPlan 定向改写）：
  action_sequence: "缓慢拿起手机 → 按下播放键 → 录音开始播放 → 
                    对方眼睛睁大、嘴唇微张 → 后退半步"
                    
其他字段不动。
```

**这就是结构化的威力：** 评测→诊断→修改，每一步都知道自己在改什么、保护什么。
