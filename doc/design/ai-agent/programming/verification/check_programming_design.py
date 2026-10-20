"""Static program-design checks only; no service/database/model is started.
Tool dependencies: upstream check_design.py deps + pglast and tomli (for Python <3.11).
"""
from pathlib import Path
from urllib.parse import unquote
import ast
import json
import re
import subprocess
import sys
try:
    import tomllib
except ImportError:
    import tomli as tomllib
from pglast import parse_sql

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[3]
MAIN = BASE.parents[1] / '学生持续学习-AI-Agent群程序设计与工程脚手架-v1.0.md'
PARENT = BASE.parents[1] / '学生持续学习-AI-Agent群详细设计-v1.0.md'


def check_markdown(path):
    text = path.read_text()
    assert text.count('```') % 2 == 0, path
    previous = None
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith('|'):
            count = line.count('|')
            if previous and previous[0] + 1 == number:
                assert previous[1] == count, (path, number)
            previous = (number, count)
    plain = re.sub(r'```.*?```', '', text, flags=re.S)
    for link in re.findall(r'\]\(([^)]+)\)', plain):
        if '://' in link or link.startswith('#'):
            continue
        assert (path.parent / unquote(link.split('#')[0])).exists(), (path, link)


def check():
    upstream = subprocess.run([sys.executable, str(BASE.parent / 'verification/check_design.py')],
                              capture_output=True, text=True, check=True)
    parent_result = json.loads(upstream.stdout)
    for md in [MAIN, PARENT, ROOT/'docs/design/README.md', *BASE.rglob('*.md')]:
        check_markdown(md)
    assert MAIN.name in PARENT.read_text() and PARENT.name in MAIN.read_text()
    blueprint = json.loads((BASE/'scaffold-blueprint.json').read_text())
    assert blueprint['status'] == 'design_only_no_generated_services'
    modules = {m['id']: m for m in blueprint['modules']}
    assert len(modules) == len(blueprint['modules'])
    visiting, visited = set(), set()
    def visit(name):
        assert name in modules, name
        assert name not in visiting, ('cycle', name)
        if name in visited:
            return
        visiting.add(name)
        for dependency in modules[name]['depends_on']:
            visit(dependency)
        visiting.remove(name)
        visited.add(name)
    for name in modules:
        visit(name)
    for rule in blueprint['forbidden_dependencies']:
        assert rule['to'] not in modules[rule['from']]['depends_on']
    schema = json.loads((BASE.parent/'contracts/learning-agent.schema.json').read_text())
    assert {r['role'] for r in blueprint['roles']} == {'LA-01','LA-02','LA-03','LA-04','LA-05'}
    for role in blueprint['roles']:
        assert role['output_definition'] in schema['$defs']
    api = json.loads((BASE.parent/'contracts/learning-agent.openapi.json').read_text())
    operation_ids = {op['operationId'] for methods in api['paths'].values() for op in methods.values()}
    assert set(blueprint['required_openapi_operation_ids']) == operation_ids
    assert {w['name'] for w in blueprint['workflows']} == {'bootstrap','attempt','review','assist'}
    assert len(blueprint['planned_make_targets']) == len(set(blueprint['planned_make_targets']))
    cases = json.loads((BASE/'component-cases.json').read_text())
    assert cases['status'] == 'test_specifications_not_runtime_results'
    assert len({c['id'] for c in cases['cases']}) == len(cases['cases'])
    req = (ROOT/'docs/requirements/通用Agentic学习与考试平台-系统需求规格说明书-v0.3.md').read_text()
    known = set(re.findall(r'\b(?:FR-[A-Z]+|AR|MAC|NFR|IR|UX|AC|T)-\d{2}\b', req))
    for case in cases['cases']:
        assert set(case['requirement_refs']) <= known, case['id']
        assert case['execution_status'] == 'not_executed_specification'
        assert case['input'] and case['expected'] and case['invariants'] and case['component']
    all_doc_refs = set(re.findall(r'\b(?:FR-[A-Z]+|AR|MAC|NFR|IR|UX|AC|T)-\d{2}\b', MAIN.read_text()))
    assert all_doc_refs <= known, all_doc_refs - known
    sql_statements = 0
    tables = []
    for sql_file in sorted((BASE/'sql').glob('*.sql')):
        statements = parse_sql(sql_file.read_text())
        sql_statements += len(statements)
        for raw in statements:
            if type(raw.stmt).__name__ == 'CreateStmt':
                tables.append(raw.stmt.relation.schemaname + '.' + raw.stmt.relation.relname)
    assert len(tables) == len(set(tables))
    for required in ['agent_runtime.agent_run','agent_runtime.run_dispatch',
                     'agent_runtime.logical_model_call','learning_coordination.execution_fence',
                     'learning_coordination.submission','learning_coordination.update_outcome']:
        assert required in tables, required
    code = (BASE/'templates/ports.py.example').read_text()
    ast.parse(code)
    compile(code, 'ports.py.example', 'exec')  # Do not import/execute nonexistent generated services.
    toml = tomllib.loads((BASE/'templates/pyproject.toml.example').read_text())
    assert toml['project']['requires-python'] == '>=3.14,<3.15'
    assert set(toml['project']['scripts']) == {'learning-agent-api','learning-agent-worker','learning-agent-rag'}
    print(json.dumps({'status':'pass','upstream_contract_checks':parent_result['status'],
                      'modules':len(modules),'agent_roles':len(blueprint['roles']),
                      'internal_operations_referenced':len(operation_ids),
                      'component_cases_specified_not_executed':len(cases['cases']),
                      'sql_statements_parsed':sql_statements,'reference_tables':len(tables),
                      'new_links_and_bidirectional_links':'pass','python_template_ast':'pass',
                      'toml_template_parse':'pass','services_or_migrations_executed':False,
                      'dependency_compatibility_or_production_verified':False}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    check()
