# -*- coding: utf-8 -*-
"""Validate documentation structure and traceability; does not test the platform."""
from pathlib import Path
import re
import json
import hashlib
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[3]
ARCH = ROOT / 'docs/architecture'
SOURCE = ROOT / 'docs/requirements/通用Agentic学习与考试平台-系统需求规格说明书-v0.1.md'
MAIN = ARCH / '通用Agentic学习与考试平台-总体架构设计-v0.1.md'
REPORT = ARCH / 'verification/文档检查报告-v0.1.md'
INDEX = ARCH / 'verification/requirement-index.json'


def check():
    source = SOURCE.read_text()
    main = MAIN.read_text()
    index = json.loads(INDEX.read_text())
    ids = [item['id'] for item in index]
    assert len(ids) == len(set(ids)) == 262
    source_ids = set(re.findall(r'^\| ((?:FR-[A-Z]+|NFR|AR|DR|IR|UX|CON|BR|AC|T|SRC)-\d+) \|', source, re.M))
    source_ids.update(re.findall(r'^- (?:\*\*)?((?:DATA|AR)-\d+)', source, re.M))
    for line in source.splitlines():
        if line.startswith(('补充接口与体验约束：', '补充约束：')):
            source_ids.update(re.findall(r'((?:IR|UX|CON)-\d+)(?=（P0）| 要求)', line))
    assert set(ids) == source_ids, (set(ids) - source_ids, source_ids - set(ids))
    assert len(re.findall(r'^## \d+\.', main, re.M)) == 23
    for n in range(1, 24):
        assert main.count(f'<a id="arch-{n:02}"></a>') == 1
    for prefix, total in [('NFR', 28), ('AC', 33), ('SRC', 17), ('T', 20), ('FR-DOM', 16), ('AR', 14), ('DATA', 14)]:
        assert all(f'{prefix}-{n:02}' in ids for n in range(1, total + 1)), prefix
    for n in range(1, 14):
        assert f'| UJ-{n:02} ' in main
    assert '| SJ-01 ' in main
    matrix = (ARCH / 'verification/需求追溯与验证矩阵-v0.1.md').read_text()
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() in matrix
    assert all(f'| {item_id}／L' in matrix for item_id in ids)
    local_links = 0
    tables = 0
    diagrams = {'flowchart': 0, 'sequenceDiagram': 0, 'erDiagram': 0, 'stateDiagram-v2': 0}
    json_examples = 0
    files = sorted(p for p in ARCH.rglob('*.md') if p != REPORT)
    for path in files:
        text = path.read_text()
        assert '\ufffd' not in text, str(path)
        assert text.count('```') % 2 == 0, str(path)
        for block in re.findall(r'(?:^\|.*\|\n)+', text, re.M):
            rows = block.splitlines()
            assert len({row.count('|') for row in rows}) == 1, (path, rows[0])
            assert any(re.match(r'^\|[\s:|-]+\|$', row) for row in rows), (path, rows[0])
            tables += 1
        for target in re.findall(r'\[[^\]\n]+\]\(([^)]+)\)', text):
            if target.startswith(('https://', 'http://', '#')):
                continue
            ref, _, anchor = unquote(target).partition('#')
            resolved = (path.parent / ref).resolve()
            assert resolved.exists() or resolved == REPORT, (path, target)
            if anchor:
                assert f'id="{anchor}"' in resolved.read_text(), (path, target)
            local_links += 1
        for block in re.findall(r'```json\n(.*?)```', text, re.S):
            json.loads(block)
            json_examples += 1
        for graph in re.findall(r'```mermaid\n(.*?)```', text, re.S):
            kind = graph.splitlines()[0].split()[0]
            assert kind in diagrams, (path, kind)
            diagrams[kind] += 1
            if kind == 'flowchart':
                declared = set(re.findall(r'\b([A-Za-z][A-Za-z0-9_]*)[\[\{]', graph))
                edges = re.findall(r'^\s*([A-Za-z][A-Za-z0-9_]*)(?:\[[^\n]*?\]|\{[^\n]*?\})?\s*--(?:>|\.->)\s*(?:\|[^|]+\|\s*)?([A-Za-z][A-Za-z0-9_]*)', graph, re.M)
                used = {node for edge in edges for node in edge}
                assert used <= declared, (path, used - declared)
                assert edges, str(path)
            elif kind == 'sequenceDiagram':
                declared = set(re.findall(r'^\s*participant\s+(\w+)', graph, re.M))
                edges = re.findall(r'^\s*(\w+)\s*-+>>?\+?-?\s*(\w+):', graph, re.M)
                assert {n for edge in edges for n in edge} <= declared, str(path)
    return {'requirement_items': len(ids), 'chapters': 23, 'learner_journeys': 13, 'support_journeys': 1,
            'acceptance_cases': 33, 'markdown_files_checked': len(files), 'markdown_tables': tables,
            'local_links': local_links, 'diagrams': diagrams, 'json_examples': json_examples,
            'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest()}


if __name__ == '__main__':
    result = check()
    lines = ['# 架构文档检查报告 v0.1', '', '日期2026-10-18；检查类型：文档结构、链接、编号及追溯自动核对＋人工设计一致性复核。', '', '## 1. 自动检查结果', '', '结果：通过。', '', '| 检查项 | 结果 |', '|---|---|']
    for key, value in result.items():
        lines.append(f'| {key} | {json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else value} |')
    lines += ['', '可复现命令：`python3 docs/architecture/verification/check_architecture_docs.py`。脚本只读取文档并更新本报告，不访问生产服务。', '', '## 2. 人工设计一致性复核', '', '| 检查 | 结论与限制 |', '|---|---|',
              '| 多Agent与业务边界 | 主文档和专项统一为协调/讲解/计划角色；领域模块校验与持久化，内容Agent可选。 |',
              '| RAG与知识库 | 母本、个人知识和检索投影分开；结构化评分与检索生成不混用，嵌入须有独立能力与数据授权。 |',
              '| 一致性与恢复 | 作答事实、消息去重、画像水位、计划CAS和外部未知副作用区分；不能承诺供应方恰好一次。 |',
              '| 质量与容量 | 全部NFR有措施和验证入口；容量与SLO为工作假设，AI并发瓶颈及降级率需实测。 |',
              '| 技术与实例 | 法考原要求保留；第二实例和具体部署待确认；Web/App按各自兼容版本，不强制同React运行时。 |',
              '| 运维与退出 | 原始事实备份、影子重建、删除账本重放、支付和内容影响均有操作设计；实际演练未执行。 |',
              '', '## 3. 未执行与待评审事项', '',
              '本报告没有安装或启动平台，没有执行代码PoC、真实API/数据库/消息测试、模型/RAG基准、性能、安全、真机或灾难恢复演练；所有实施验收状态仍为未执行。', '',
              'Mermaid仅检查围栏、图类型、引用节点和参与者等结构；未使用完整Mermaid解析器或浏览器渲染，因此不把结构检查称为图形渲染验收。JSON示例已做语法解析，但尚未生成完整OpenAPI、JSON Schema或DDL。', '',
              '需求T-01～20和架构假设A-01～06需在相应交付前闭合。建议技术基线已以官方公开资料核验，但完整依赖兼容、许可证、供应方地区和运行成本仍需实际锁定验证。', '',
              '逐条映射证明文档中存在设计落点，不能证明实现已经满足要求；详细测试用例、执行ID和上线签收仍需各角色完成。', '']
    REPORT.write_text('\n'.join(lines))
    print(json.dumps(result, ensure_ascii=False, indent=2))
