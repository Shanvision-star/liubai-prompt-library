"""将人工逐条撰写的教学笔记编排成卡片；不调用模型、不推断新条目分析。"""

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEARNING = ROOT / "learning-library"

# 前34条采用阅读后的结构摘要；后续站点素材使用已经区分“原/建议”的公开整理。
STRUCTURES = {
    1: ["目标：有边界地完成开发协作", "输入：当前主线、权威文档、仓库现状、任务与范围", "步骤：审计实际缺口→最小改动→验证→同步文档", "约束：分支隔离、保留已有修改、模拟与实际执行分开", "输出与验收：具体变更、证据、未验证事项；按任务选择最便宜有效检查"],
    2: ["目标：评价设计并提出可行动取舍", "输入：作品、受众、任务、品牌约束", "步骤：观察/推断/偏好分开；保留优点，再处理最重要问题", "输出：位置、证据、影响、最小修改与复查", "边界：审美偏好不能写成普遍事实；无新证据不无限循环"],
    3: ["目标：减少无助于任务的负担", "步骤：保留/删除/合并/延后分别决策", "约束：事实、关键任务、错误恢复和可访问性保留", "输出：每项删改的理由和影响", "验收：相同任务在删改后仍能完成，不能只比较字数"],
    4: ["目标：选择视觉方向", "输入：真实内容、受众、品牌与可用素材", "步骤：固定内容比较三个方向→选一处样张→再扩展", "输出：字体、色彩角色、材质、优势与代价", "边界：参考与提案不冒充品牌现有规则；效果未渲染时明确标注"],
    5: ["目标：建立可复用主题", "输入：媒介、受众、语气、已有品牌规则和选定主题", "步骤：未选主题时比较候选；已选时核对定义后应用", "输出：颜色与字体的语义角色、回退与样张", "验收：相同中文内容、层级与状态表达；未测不报对比度数值"],
    6: ["目标：让受众完成页面主要任务", "输入：真实内容、设计边界、现有组件与技术栈", "步骤：核心信息与动作→骨架→实现→状态与交互检查", "约束：不伪造客户、交易、评价和成功状态", "输出：界面及具体证据；设计稿和实际交互实现分开"],
    7: ["目标：从现有设计提取可复用规则", "输入：截图、CSS、设计文件或代码中的可读证据", "输出：名称、角色、值、来源与可信程度", "约束：现状与建议分开；未知字体和断点不伪装实测", "验收：用不同页面或组件抽查，并保留冲突"],
    8: ["目标：不同视口和输入方式下任务成立", "输入：现有页面、必须保留内容、允许修改范围", "步骤：建立情境矩阵→修复最大任务障碍→复查原场景", "约束：不只缩小桌面版，不以隐藏关键功能代替适配", "输出：目标场景证据；模拟尺寸不等于真实设备验证"],
    9: ["目标：加固边界与恢复状态", "输入：关键动作、接口和权限约束、支持场景", "步骤：状态/触发/反馈/可操作/恢复/证据矩阵", "约束：保留输入；不把加载、空结果、失败混在一起", "验收：复测失败路径和正常路径；禁用按钮不等于服务端幂等"],
    10: ["目标：基于服务与长期价值做商业判断", "输入：客户任务、当前方案、基线、成本与证据", "步骤：理解需求→比较替代→定义范围、责任和退出", "约束：允许更小方案或不采购；不捏造收益", "输出：事实、假设、取舍与下一步；真实结果另行验证"],
    11: ["目标：删掉重复微文案", "约束：保留表单标签、错误反馈与控件可访问名称", "关键关系：视觉省略不等于移除语义名称", "输出：具体删改位置及保留理由", "验收：截图、键盘与可访问名称分别检查；不能只凭视觉通过"],
    12: ["类型：外部技能的资源入口", "已知：仓库或文件定位线索", "未知：未取得正文不能补写其结构、步骤和效果", "下一步：定位实际文件、版本、许可与所需依赖", "验收：能引用一项实际约束并解释适用任务"],
    13: ["输入：8–12个UI状态、黑白或一强调色、约120BPM音乐", "方向：同一形状零切镜，光标先操作，极轻微过冲", "步骤：组件序列按节拍展开；状态与内部动作需分开", "实现：单HTML、seek(t)、闭式弹簧与可重复采样", "验收：先每拍静帧再全片；文字出入独立；头尾光标与运动接续"],
    14: ["输入：产品URL、真实数据、状态、品牌和输出比例", "约束：单draw(t)，无计时器或跨帧状态，同一形状", "结构：身份确认、加载、用户/匹配、操作与回归", "实现：文字先退后进，强调对象跨状态迁移", "验收：先接触表静帧；60fps多子帧导出；各比例仍需重查布局"],
    15: ["输入：实际Sprites网站UI与广告资料", "结构：连接账户→研究→审批→预算→暂停", "视觉：暖灰、黑白、橙色与轻微弹簧", "实现：seek(t)、光标操作、合成UI声音，无音乐", "边界：竞品数量与图表数据需核对；画面示例不是营销效果证明"],
    16: ["目标：GSAP卡片入场时间线", "数值：卡片280ms、标题220ms、元信息160ms、错峰60ms", "检查：Playwright逐帧查看，比较过冲或错误", "修正：定位后局部修补，不重写全部", "缺口：原文未给总轮次上限、比较阈值与完整开始时刻"],
    17: ["输出：14秒、1440方形、60fps、Canvas2D循环", "输入：色值、圆角、字体与状态", "时序：0.5秒网格，形状0.35秒与相机0.6秒收稳", "实现：renderAt(t)纯函数，禁随机数/时钟/跨帧状态", "检查：先故事板；每拍前后5帧；光标、字形和循环接缝"],
    18: ["结构：卡片30%→100%缩放并显现，稳定后细节逐个进入", "动作：曲线描边，两个矩形错时运动形成光效", "层级：容器先建立，数据随后可读，背景光辅助", "缺口：未给时长、曲线、真实数据与输出规格", "验收建议：文字在何时开始可读，各层是否争夺视线"],
    19: ["输入：单词品牌名、强调色与约120BPM曲目", "结构：输入条→进度环→时间轴→预览→通知→输入条", "输出：1440方形，24拍；原文含编码与响度要求", "实现：同一圆角矩形的连续属性链、seek(t)、文字裁切", "检查：先每拍静帧；文字不重叠，光标头尾接续"],
    20: ["输出：30秒、1080方形、60fps、MP4", "输入：音乐文件路径与8–12个状态", "步骤：测BPM、拍点、高潮→选下拍开始的30秒→排动作", "约束：同一对象零切镜，光标先点击或拖动，轻过冲", "实现：4个子帧混合；缺口是具体状态、品牌与曲目"],
    21: ["类型：日语UI变形提示词", "输入：状态、单强调色、约120BPM曲目", "字体：日文Noto Sans JP与拉丁Geist，角色应明确", "结构：同一形状、光标操作、组件与节拍序列", "实现与验收：seek(t)、子帧、独立文字时序与循环接缝；语言适配需重查"],
    22: ["结构：黑底一点→多交易窗口→多尺度缩放→横向移动端", "内容：图表、持仓、期权链、观察列表", "实现：JavaScript；结尾品牌句", "缺口：窗口真实数据、具体轨迹与可测风格条件", "边界：描述中的时间文本不能替代完整交付规格；桌面与手机布局需分别验证"],
    23: ["输出：12秒、1920×1080、30fps、HTML seek(t)", "结构：输入→12格弹球姿态胶片→播放头→标题→球成为句号", "声音：键击、确认、逐格音高上升与落点声", "约束：白黑橙、手机可读、2–4帧错峰、快速动作才模糊", "验收：先5张关键帧，批评后修最差3项，再渲染；连续片段仍需看"]
}


def read_text(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return handle.read()


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def binding(root, entry_id):
    index = json.loads(read_text(root / "index.json"))
    item = next(row for row in index["entries"] if row["id"] == entry_id)
    record_path = root / item["record_file"]
    record = json.loads(read_text(record_path))
    return {"version": item["latest_version"], "original_sha256": digest(read_text(record_path.parent / record["original"]["file"])), "optimized_sha256": digest(read_text(root / item["optimized_file"]))}


def load_notes():
    notes = {}
    for line in read_text(LEARNING / "editorial-notes.psv").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) != 6 or int(parts[0]) in notes:
            raise ValueError("教学笔记有重复编号或字段数不对")
        notes[int(parts[0])] = parts[1:]
    return notes


def card(number, title, note, profile, original, revision):
    method, focus, reasoning, counter, transfer = note
    source_number = number - 11 if 24 <= number <= 34 else number
    if source_number in STRUCTURES:
        structure = STRUCTURES[source_number]
        evidence_scope = "以下是已读原文与当前保存/改编版的结构摘要；改编要求不冒充原作者原话。"
    else:
        facts = [line[2:] for line in original.splitlines() if line.startswith("- **")]
        # 公开版事实已区分原要求与整理建议；这里只编排，不抓取受限站点全文。
        structure = facts
        evidence_scope = "以下摘自本库已保存的原创整理。“原”是当时记录的来源要求，“建议”是整理者补充，标题题材不自动算原文要求。"
    if not structure:
        raise ValueError(f"PRM-{number:04d} 缺少结构证据")
    exercise, marker, answer = transfer.partition("参考")
    related = ""
    if 13 <= number <= 23:
        related = f"\n\n[对照中文改编 PRM-{number+11:04d}](/?entry=PRM-{number+11:04d}&tab=analysis)"
    elif 24 <= number <= 34:
        related = f"\n\n[对照原文条目 PRM-{number-11:04d}](/?entry=PRM-{number-11:04d}&tab=analysis)"
    return f"""# {focus}

这是 AI 基于本条保存内容撰写的教学分析。设计解释是分析推断，不代表作者未公开的思考；对照与改写均为待验证建议，未运行成片或模型效果测试。

## 原文怎样组织任务

{evidence_scope}

""" + "\n".join("- " + item for item in structure) + f"""

## 为什么这样写

{reasoning}

### 可以迁移的设计方法

**{profile['name']}**

{profile['principle']}

### 艺术与表达上的取舍

{profile['tradeoff']}

这些是本次提出的判断依据，不能据此反推源作者一定采用了相同方法。阅读时把“原文有这个要求”和“我认为这个要求会产生这个影响”分开。

## 只改一个条件，会发生什么

{counter}

以上是机制分析下的预期，不是已跑出的A/B结果。若验证，保持同一任务、素材和其余参数，记录实际输出与反例；不能用一份更长的提示词自动证明更有效。

## 换成自己的项目

{exercise}

先写出保留的一条结构、需要替换的一项输入，以及这样改的理由，再看参考思路。

### 参考思路

{answer if marker else '保留本条解释的关系，而不是机械复制品牌、配色和参数。'}

### 可改写的提示词骨架

```text
{profile['template']}
本次重点：{focus}。
先说明一项设计取舍，再给输出。把原文事实、分析推断与新增提案分开；未知资料不补造。
```

骨架是方法起点，必须填入上面的具体任务和材料。单纯替换产品名仍可能缺受众、真实内容与验收条件。

## Loop：检查什么，怎样停止

阅读练习不需要生成循环：能解释本条的一个取舍并完成迁移即可。实际制作建议最多两轮，源提示词若有更严格上限则从其约束。

1. 固定任务、素材和比较条件，先做最小样张或关键片段。检查：{profile['checks']}。
2. 结合上面的单变量对照，只修一项有具体证据的问题，记录改前、改后和未改善项，再复查相同片段。
3. 目标满足即停止；同一问题没有新证据、关键材料缺失或达到两轮时停止并说明缺口。没有实际渲染或用户结果，状态仍为 untested。

动画首尾循环与修改Loop是不同概念：前者描述播放接续，后者描述检查与修正；本条不要求循环播放时，不额外制造首尾接缝任务。

[回到学习路线](/?entry=PRM-0222&tab=analysis){related}

教学版本 {revision} · 对应内容通过清单哈希绑定 · 来源与原文见本条对应页面。
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-library", type=Path, help="额外绑定经核对的本地素材版本，不修改它")
    parser.add_argument("--revision", default="v001", help="教学版本；已存在不同内容时须使用新版本")
    args = parser.parse_args()
    if not re.fullmatch(r"v\d{3,}", args.revision):
        parser.error("revision必须为v001等版本号")
    notes = load_notes()
    profiles = json.loads(read_text(LEARNING / "methods.json"))
    public = ROOT / "bundled-library"
    entries = json.loads(read_text(public / "index.json"))["entries"]
    if {int(row["id"].split("-")[1]) for row in entries} != set(notes):
        raise ValueError("公开素材与逐条笔记编号不一致；新素材必须先实际阅读撰写")
    manifest = {"schema_version": 1, "revision": args.revision, "evaluation_status": "untested", "entries": {}}
    for item in entries:
        entry_id = item["id"]
        number = int(entry_id.split("-")[1])
        record_path = public / item["record_file"]
        record = json.loads(read_text(record_path))
        original = read_text(record_path.parent / record["original"]["file"])
        if number == 222:
            text = read_text(LEARNING / "learning-route.md")
        else:
            text = card(number, item["title"], notes[number], profiles[notes[number][0]], original, args.revision)
            if number == 218:
                text += "\n\n" + read_text(LEARNING / "token-bucket-worked-example.md")
        path = LEARNING / "cards" / entry_id / (args.revision + ".md")
        path.parent.mkdir(parents=True, exist_ok=True)
        data = text.encode("utf-8")
        if path.exists() and path.read_bytes() != data:
            raise ValueError(f"{path} 已存在，不能覆盖不可变教学版本；使用新的--revision")
        path.write_bytes(data)
        signatures = [binding(public, entry_id)]
        if args.source_library:
            signature = binding(args.source_library, entry_id)
            if signature not in signatures:
                signatures.append(signature)
        manifest["entries"][entry_id] = {"revision": args.revision, "file": path.relative_to(LEARNING).as_posix(), "sha256": hashlib.sha256(data).hexdigest(), "bindings": signatures, "method": notes[number][0]}
    (LEARNING / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"cards": len(entries), "revision": args.revision, "effectiveness": "untested"}))


if __name__ == "__main__":
    main()
