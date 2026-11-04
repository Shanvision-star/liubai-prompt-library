"""从既有私人摘录及用户提供原稿修复来源层，保留旧正文与版本，不联网抓取全文。"""
import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
import zipfile
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from reference_store import ReferenceStore


def section(text, heading):
    match=re.search(r"^## " + re.escape(heading) + r"\s*\n(.*?)(?=^## |\Z)",text,re.M|re.S)
    return match[1].strip() if match else ""


def explanation(quote, design, full):
    q=quote.lower()
    reasons=[]
    for tokens,reason in [
        (("pure function", "deterministic"),"时间决定画面状态，可重复抽取同一帧；应比较同一时间点的两次渲染，而不只看播放是否流畅。"),
        (("canvas", "no libraries"),"绘制环境约束决定实现路径；先验证所用 API 和依赖，再讨论视觉风格。"),
        (("loop", "seamless"),"循环需要首尾的位置、速度与颜色连续；测试接缝，不能只检查单次播放。"),
        (("morph", "transform"),"形变通过持续保留轮廓或视觉锚点帮助观众追踪对象；先确定对应关系，再安排过渡。"),
        (("text", "type", "typography", "letter"),"文字既是信息也是运动主体；运动不能挤占阅读时间，要检查停留时长、行宽与对比度。"),
        (("ui", "dashboard", "app", "product"),"产品状态变化要让观众读懂操作和反馈；应使用核实过的界面或明确标注的示例数据。"),
        (("camera", "3d", "zoom"),"镜头改变注意力与空间关系；先选一个主运动，避免多个方向同时争夺焦点。"),
        (("physics", "simulation", "spring"),"运动规律应由参数或方程控制，检查边界和重复性；视觉上的自然不等于物理结果准确。"),
        (("music", "note", "sound", "collision"),"声音与可见动作需要有明确对应关系；例如撞击触发音符时，应逐个检查发生时刻与声音同步，避免只加一条无关背景音乐。"),
        (("10 seconds", "10 segundos", "seconds"),"总时长会限制信息量；逐镜计算阅读与转场时间，不能无限塞入卖点。"),
        (("logo", "brand"),"品牌识别依赖稳定的轮廓和留白；先保留识别锚点，再安排强调与退出。"),
    ]:
        if any(re.search(r'(?<!\w)'+re.escape(token)+r'(?!\w)',q) for token in tokens): reasons.append(reason)
    if not reasons: reasons=["先从提示词中提取交付物与可检查条件；只有风格形容词时，需要补充输入、主体和验收方式。"]
    scope="已保存的完整短提示词" if full else "已保存的短摘录与历史整理记录"
    return f"# 来源文本拆解\n\n## 依据与范围\n\n本次依据：{scope}。逐条结构记录来自此前整理，后面的约束解释是按具体词语匹配的初步建议，尚未逐条人工验收。以下推理为整理者分析；未观看或测量作者的完整创作过程，也未验证生成效果。\n\n" + (f"文本证据：\n\n> {quote}\n\n" if quote else "该条是来源索引，不构成制作提示词。\n\n") + "## 已有逐条结构记录\n\n" + (design or "该索引用于找到各个来源页面。") + "\n\n## 这些约束为什么影响设计\n\n" + "\n\n".join(reasons) + "\n\n## 输入缺口与复现检查\n\n把文本明示要求与推断分开；未指定的时长、画幅、素材、字体、配色、工具和音频均需另行确认。先做一个代表镜头，再核对可读性、动作衔接、状态准确性及输出规格；最多修正两轮。未制作对照视频时，不能将这些建议写成已证实效果。\n"


def repair(source, target, provided, report_path, apply=False):
    index=json.loads((target/'index.json').read_text(encoding='utf-8-sig'))
    now=datetime.now().astimezone().isoformat(timespec='seconds')
    rows=[]; planned=[]
    for item in index['entries']:
        record_path=(target/item['record_file']).resolve()
        if not record_path.is_relative_to(target): raise ValueError('记录路径越出目标库')
        record=json.loads(record_path.read_text(encoding='utf-8-sig'))
        url=record.get('source',{}).get('url') or ''
        if 'prompt-motion.com' not in url: continue
        old=source/item['record_file']
        if not old.is_file(): raise ValueError('缺少私人来源记录：'+item['id'])
        original_record=json.loads(old.read_text(encoding='utf-8-sig'))
        if original_record.get('source',{}).get('url') != url: raise ValueError('来源不匹配')
        text=(old.parent/original_record['original']['file']).read_text(encoding='utf-8-sig')
        quote='\n'.join(re.findall(r'^> ?(.*)$',section(text,'原语言短引与中文'),re.M))
        translated=re.search(r'^中文(?:译文|释义)：(.*)$',text,re.M)
        translated=translated[1].strip() if translated else ''
        old_hash=re.search(r'原网站正文 SHA-256[：:]([a-f0-9]{64})',text)
        full=bool(quote and len(quote.split())<=25 and old_hash and sha256(quote.encode()).hexdigest()==old_hash[1])
        basis='preserved_short_prompt_hash_verified' if full else 'preserved_excerpt_only'
        override=provided.get(item['id'])
        if override:
            if override['url'] != url or override['evidence_basis'] not in ('user_supplied_screenshot','verified_short_web_prompt'):
                raise ValueError('原稿来源或核对依据不合法')
            quote,translated=override['original'],override['translation']
            if override['evidence_basis']=='verified_short_web_prompt' and len(quote.split())>25: raise ValueError('短引超限')
            basis=override['evidence_basis'];full=True
        is_index=url.rstrip('/')=='https://prompt-motion.com' or item['id']=='PRM-0222'
        status='source_index' if is_index else 'complete' if full else 'excerpt_only'
        author=re.search(r'- (@[^｜\s]+)',text)
        post=re.search(r'\((https://x\.com/[^)]+)\)',text)
        metadata={'schema_version':1,'status':status,'evidence_basis':basis,'checked_at':now,
                  'author':author[1] if author else '', 'post_url':post[1] if post else None,
                  'excerpt':'' if full else quote,'excerpt_translation':'' if full else translated,
                  'notice':'本机私人来源层；来源归属与公开分发许可单独核对。' if full else '来源全文尚未收录。这里仅显示既有摘录及释义，请从原网页查看全文；旧整理稿保存在复用改写中。'}
        files={}
        def put(key,name,value):
            data=value.encode('utf-8');files[name]=data;metadata[key+'_file']=name;metadata[key+'_sha256']=sha256(data).hexdigest()
        if full:
            if not translated: raise ValueError('完整原文没有对应译文')
            put('original','SOURCE-PROMPT.txt',quote)
            put('translation','SOURCE-PROMPT.zh.txt',translated)
            metadata['translation_source_sha256']=metadata['original_sha256']
        analysis=override.get('analysis') if override else None
        analysis=analysis or explanation(quote,section(text,'设计思路拆解'),full)
        put('analysis','SOURCE-PROMPT-ANALYSIS.md',analysis)
        record['motion_source']=metadata
        planned.append((record_path,record,files,sha256(record_path.read_bytes()).hexdigest()))
        rows.append({'id':item['id'],'status':status,'evidence_basis':basis,'url':url,'original_sha256':metadata.get('original_sha256')})
    report={'created_at':now,'count':len(rows),'complete':sum(r['status']=='complete' for r in rows),
            'excerpt_only':sum(r['status']=='excerpt_only' for r in rows),'source_index':sum(r['status']=='source_index' for r in rows),'entries':rows}
    if apply:
        backup=report_path.with_suffix('.records-before.zip')
        if backup.exists(): raise ValueError('备份已存在，请先核对已有执行')
        store=ReferenceStore(target)
        with store._locked():
            for path,_,files,expected in planned:
                if sha256(path.read_bytes()).hexdigest()!=expected: raise ValueError('记录已被修改，请重新核对后再迁移：'+str(path))
                for name in files:
                    if (path.parent/name).exists(): raise ValueError('来源层已存在，不覆盖：'+str(path.parent/name))
            with zipfile.ZipFile(backup,'x',zipfile.ZIP_DEFLATED) as archive:
                for path,_,_,_ in planned: archive.write(path,path.relative_to(target).as_posix())
            changes={}
            for path,record,files,_ in planned:
                current=json.loads(path.read_text(encoding='utf-8-sig'));current['motion_source']=record['motion_source']
                changes[path.relative_to(target).as_posix()]=(json.dumps(current,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
                for name,data in files.items(): changes[(path.parent/name).relative_to(target).as_posix()]=data
            store._transaction(changes)
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='entries'},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--target',type=Path,required=True)
    p.add_argument('--provided',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--apply',action='store_true')
    a=p.parse_args();repair(a.source.resolve(),a.target.resolve(),json.loads(a.provided.read_text(encoding='utf-8-sig')),a.report.resolve(),a.apply)
