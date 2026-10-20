# -*- coding: utf-8 -*-
"""Check current 4A documents and immutable archive, not implementation quality."""
from pathlib import Path
from collections import Counter
from urllib.parse import unquote
import hashlib,json,re

ROOT=Path(__file__).resolve().parents[3]
ARCH=ROOT/'docs/architecture'
REQ=ROOT/'docs/requirements/通用Agentic学习与考试平台-系统需求规格说明书-v0.3.md'
REPORT=ARCH/'verification/4A-文档检查报告-v1.0.md'


def definitions(text):
    ids=re.findall(r'^\| ((?:FR-[A-Z]+|MAC|NFR|AR|DR|IR|UX|CON|BR|AC|T|SRC)-\d+) \|',text,re.M)
    ids+=re.findall(r'^- (?:\*\*)?((?:DATA|AR)-\d+)',text,re.M)
    for line in text.splitlines():
        if line.startswith(('补充接口与体验约束：','补充约束：')):
            ids+=re.findall(r'((?:IR|UX|CON)-\d+)(?=（P0）| 要求)',line)
    assert len(ids)==len(set(ids)),[k for k,v in Counter(ids).items() if v>1]
    return set(ids)


def check():
    req=REQ.read_text()
    ids=definitions(req)
    old=ROOT/'docs/requirements/通用Agentic学习与考试平台-系统需求规格说明书-v0.2.md'
    old_ids=definitions(old.read_text())
    assert len(old_ids)==341 and old_ids<=ids
    assert len(ids)==377
    assert hashlib.sha256(old.read_bytes()).hexdigest()=='27afb11ba81ba4aa8618756a2592b02707ab529738be860032ee3a5af30004fd'
    for prefix,total in [('AC',57),('NFR',36),('T',27),('SRC',19),('FR-BOP',3),('FR-KOP',10),('FR-ADM',5),('DR',26),('MAC',14)]:
        assert all(f'{prefix}-{n:02}' in ids for n in range(1,total+1)),prefix
    refs=set(re.findall(r'\b(?:FR-[A-Z]+|MAC|NFR|AR|DR|IR|UX|CON|BR|AC|T|SRC|DATA)-\d{2}\b',req))
    assert refs<=ids,refs-ids
    index=json.loads((ARCH/'verification/4A-requirement-index-v1.0.json').read_text())
    assert {x['id'] for x in index['items']}==ids
    assert index['sha256']==hashlib.sha256(REQ.read_bytes()).hexdigest()
    matrix=(ARCH/'verification/4A-需求追溯与验证矩阵-v1.0.md').read_text()
    assert all(f'| {id}/L' in matrix for id in ids)
    assert all(x['status'] in ('design_mapped_unverified','pending_decision') for x in index['items'])
    for n in range(1,16): assert f'| UJ-{n:02} |' in matrix
    for n in range(1,5): assert f'| SJ-{n:02} |' in matrix
    main=(ARCH/'通用Agentic学习与考试平台-4A总体架构设计-v1.0.md').read_text()
    assert all(x in main for x in ('## 2. 业务架构 BA','## 3. 应用架构 AA','## 4. 数据架构 DA','## 5. 技术架构 TA'))
    assert '<a id=' not in main and '<a id=' not in req
    assert re.search(r'^\| MAC-14 \| P0 \|',req,re.M)
    archive=ARCH/'archive/2026-10-18-pre-4a'
    manifest=json.loads((archive/'manifest.json').read_text())
    for record in manifest['files']:
        assert hashlib.sha256((archive/record['path']).read_bytes()).hexdigest()==record['sha256'],record['path']
    current_files=[ARCH/'README.md',ARCH/'通用Agentic学习与考试平台-4A总体架构设计-v1.0.md',ARCH/'4A-关键契约与实施约束-v1.0.md',ARCH/'4A-架构决策与实施门禁-v1.0.md',ARCH/'verification/4A-需求追溯与验证矩阵-v1.0.md',ROOT/'docs/requirements/README.md',REQ]
    # Check all archive/stub links too, without changing archived bytes or executing old scripts.
    link_files=sorted(set(ARCH.rglob('*.md'))|{ROOT/'docs/requirements/README.md',REQ})
    links=0
    for path in link_files:
        if path==REPORT:continue
        for target in re.findall(r'\[[^\]\n]+\]\(([^)]+)\)',path.read_text()):
            if target.startswith(('https://','http://','#')):continue
            ref,_,fragment=unquote(target).partition('#')
            dest=(path.parent/ref).resolve()
            assert dest.exists() or dest==REPORT,(path,target)
            if fragment:assert f'id="{fragment}"' in dest.read_text(),(path,target)
            links+=1
    diagrams={'flowchart':0,'sequenceDiagram':0,'erDiagram':0}
    table_count=0;json_count=0
    for path in current_files:
        text=path.read_text();assert '\ufffd' not in text
        assert text.count('```')%2==0,path
        for table in re.findall(r'(?:^\|.*\|\n)+',text,re.M):
            rows=table.splitlines()
            assert len({r.count('|') for r in rows})==1,(path,rows[0])
            assert any(re.match(r'^\|[\s:|-]+\|$',r) for r in rows),(path,rows[0])
            table_count+=1
        for block in re.findall(r'```json\n(.*?)```',text,re.S):json.loads(block);json_count+=1
        for graph in re.findall(r'```mermaid\n(.*?)```',text,re.S):
            kind=graph.splitlines()[0].split()[0];assert kind in diagrams,kind;diagrams[kind]+=1
            if kind=='flowchart':
                nodes=set(re.findall(r'\b([A-Za-z][A-Za-z0-9_]*)[\[\{]',graph))
                edges=re.findall(r'^\s*([A-Za-z][A-Za-z0-9_]*)(?:\[[^\n]*?\]|\{[^\n]*?\})?\s*-->\s*(?:\|[^|]+\|\s*)?([A-Za-z][A-Za-z0-9_]*)',graph,re.M)
                assert {n for edge in edges for n in edge}<=nodes,(path,graph)
            elif kind=='sequenceDiagram':
                nodes=set(re.findall(r'^\s*participant\s+(\w+)',graph,re.M))
                edges=re.findall(r'^\s*(\w+)\s*-+>>?\s*(\w+):',graph,re.M)
                assert {n for edge in edges for n in edge}<=nodes,path
    return {'source_items':len(ids),'retained_v02_items':len(old_ids),'new_items':len(ids-old_ids),'changed_priority':'MAC-14 P1→P0',
            'learner_journeys':15,'support_journeys':4,'acceptance_cases':57,'nfr_items':36,
            'archived_files_byte_verified':len(manifest['files']),'checked_local_links':links,
            'current_markdown_tables':table_count,'diagrams_in_requirements_and_architecture':diagrams,'parsed_json_examples':json_count,
            'source_sha256':index['sha256']}


if __name__=='__main__':
    result=check()
    rows=['# 4A文档检查报告 v1.0','','日期：2026-10-18。范围：当前需求v0.3、新4A架构与附件、逐项追溯、历史归档。','','## 1. 自动核对','','结果：通过。','','| 检查项 | 结果 |','|---|---|']
    for k,v in result.items():rows.append('| '+k+' | '+(json.dumps(v,ensure_ascii=False) if isinstance(v,dict) else str(v))+' |')
    rows+=['','复现：`python3 docs/architecture/verification/check_4a_documents.py`。脚本只读现行文档与归档并更新本报告，不执行旧检查脚本、不修改归档原文、不访问生产系统。', '',
           '## 2. 设计一致性复核','','| 业务问题 | 四层落点与结果 |','|---|---|',
           '| 学生前台与学习Agent群 | BA学习价值流；AA学生/协作/学习/画像/计划；DA证据与版本；TA受控任务和存储。 |',
           '| 主动知识运营与人工学科负责 | BA发现/分析/审校/发布/影响；AA来源/知识工作台；DA原文、建议、审批、适用时间；TA受控接入和发布栅栏。MAC-14明确升级P0小范围闭环。 |',
           '| 来源失败与最新适用 | 成功有变化、成功无变化、失败/受限分开；发布、生效、考试/课程适用与历史口径分开，不用失败刷新最近成功。 |',
           '| 系统管理员边界 | 管理入口、技术配置与风险停用独立授权，不能以system_admin绕过学科审批或私人资料最小访问。 |',
           '| 一致性与业务恢复 | 提交事务、幂等事件、画像水位、计划预算、未知费用、人工发布/个人影响与删除重放有对应契约和处置计划。 |',
           '| 可读性 | 正文先解释四部分业务，再BA→AA→DA→TA，并以三个跨层场景串联；现行主文档和需求不添加原始HTML锚点。 |',
           '', '## 3. 限制与未完成的实施验证', '',
           '这不是平台测试通过报告。代码PoC、真实抓取、模型/RAG/画像效果、压力、安全、真机、支付对账和恢复演练均未执行；逐项矩阵状态为设计映射或待决策。T-01～27和部署/团队/预算等假设需在对应交付前闭合。', '',
           'Mermaid仅检查围栏、图类型和节点/参与者引用等结构，未使用完整解析器或浏览器渲染，不能声称视觉排版已验收。JSON示例只做语法解析，完整OpenAPI/schema/DDL和机器契约仍需E0生成与执行。', '',
           '归档逐字节SHA-256校验通过，原目录关系与关联需求快照保留；旧Markdown路径只是导航。旧归档检查结果不适用于新基线。技术来源及支持线已按主文档说明核验，但完整依赖兼容与实际服务/地区/许可仍需安装前检查。','']
    REPORT.write_text('\n'.join(rows))
    print(json.dumps(result,ensure_ascii=False,indent=2))
