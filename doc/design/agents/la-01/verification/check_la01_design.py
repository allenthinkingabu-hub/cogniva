"""Validate LA-01 design artifacts; fixture gate is not a deployed classifier.
Requires jsonschema/openapi-spec-validator and upstream checker requirements.
"""
from pathlib import Path, PurePosixPath
import copy
import json
import re
import subprocess
import sys
from urllib.parse import unquote
from datetime import datetime
from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import OpenAPIV31SpecValidator

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[3]
MAIN = BASE.parent / 'LA-01-学习协调Agent-需求与C4详细设计-v1.0.md'
PARENT = ROOT / 'docs/design/学生持续学习-AI-Agent群详细设计-v1.0.md'


def load(relative):
    return json.loads((BASE / relative).read_text())


def check_markdown(path):
    text = path.read_text()
    assert text.count('```') % 2 == 0, path
    previous = None
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith('|'):
            count = line.count('|')
            if previous and previous[0] + 1 == n:
                assert previous[1] == count, (path, n)
            previous = (n, count)
    plain = re.sub(r'```.*?```', '', text, flags=re.S)
    for link in re.findall(r'\]\(([^)]+)\)', plain):
        if '://' in link or link.startswith('#'):
            continue
        assert (path.parent / unquote(link.split('#')[0])).exists(), (path, link)


def gate(context, proposal, catalog):
    """Executable design assertion, not NLU or a runtime authorization substitute."""
    if context['page_action'] != 'free_text':
        return 'bypass_java'
    intent = proposal['intent']
    if intent == 'unsupported':
        return 'deny'
    if intent == 'clarify':
        return 'clarify'
    candidates = {x['candidate_id']: x for x in context['scope_candidates']}
    selected = proposal['scope_candidate_ids'][0]
    if selected not in candidates:
        return 'deny'
    candidate = candidates[selected]
    if not candidate['is_current']:
        return 'clarify'
    if candidate['goal_ref'] != context['input_refs']['goal_ref']:
        return 'deny'
    if candidate['manifest_ref'] != context['input_refs']['manifest_ref']:
        return 'deny'
    template = next(t for t in catalog['templates'] if t['intent'] == intent)
    if template['template_ref'] not in context['allowed_template_refs']:
        return 'clarify'
    if not set(template['required_capabilities']) <= set(context['capability_refs']):
        return 'clarify'
    if not set(template['required_preconditions']) <= set(context['precondition_refs']):
        return 'clarify'
    return 'allow'


def validate_plan(plan, context, catalog):
    assert plan['template_ref'] in context['allowed_template_refs']
    assert plan['catalog_version'] == catalog['catalog_version']
    assert plan['context_revision'] == context['context_revision']
    assert plan['auth_revision'] == context['auth_revision']
    assert plan['input_refs'] == context['input_refs']
    assert datetime.fromisoformat(plan['deadline_at'].replace('Z','+00:00')) <= datetime.fromisoformat(context['deadline_at'].replace('Z','+00:00'))
    template = next(t for t in catalog['templates'] if t['template_ref'] == plan['template_ref'])
    actual = []
    for binding in plan['step_bindings']:
        assert binding['input_refs'] == plan['input_refs']
        actual.append({k:v for k,v in binding.items() if k != 'input_refs'})
    assert actual == template['steps'], 'Template steps/executors/dependencies cannot be altered'



def budget_assembly(manifest):
    """Synthetic count-based assertion; not a tokenizer or semantic compressor."""
    budget = manifest['total_window_budget'] - manifest['output_reserve'] - manifest['safety_reserve']
    fragments = manifest['fragments']
    assert len({f['fragment_ref'] for f in fragments}) == len(fragments)
    protected = [f for f in fragments if f['protected']]
    assert set(manifest['protected_fact_refs']) <= {f['fragment_ref'] for f in protected}
    if sum(f['token_count'] for f in protected) > budget:
        return 'context_insufficient', []
    selected = [f['fragment_ref'] for f in protected]
    used = sum(f['token_count'] for f in protected)
    for f in sorted((x for x in fragments if not x['protected']), key=lambda x:(x['priority'],x['fragment_ref'])):
        if used + f['token_count'] <= budget:
            selected.append(f['fragment_ref'])
            used += f['token_count']
    return 'ready', selected


def check_engineering(text):
    engineering_schema = load('contracts/agentic-engineering.schema.json')
    Draft202012Validator.check_schema(engineering_schema)
    cases = load('examples/agentic-engineering-cases.json')
    def validate(name, value):
        selected = copy.deepcopy(engineering_schema)
        selected['$ref'] = '#/$defs/' + name
        return list(Draft202012Validator(selected,format_checker=FormatChecker()).iter_errors(value))
    for kind in ('valid','invalid'):
        for case in cases[kind]:
            assert (not validate(case['definition'],case['value'])) == (kind=='valid'),case['id']
    for case in cases['context_cases']:
        assert not validate('ContextManifest',case['manifest'])
        decision,selected = budget_assembly(case['manifest'])
        assert decision == case['expected'],case['id']
        if decision=='ready':
            assert set(case['manifest']['protected_fact_refs']) <= set(selected)
            assert selected==case['manifest']['selected_refs']
    for case in cases['memory_cases']:
        record=case['record']; assert not validate('MemoryRecord',record)
        allowed=(record['status']=='active' and
                 all(record[k]==v for k,v in case['scope'].items()) and
                 datetime.fromisoformat(record['expires_at'].replace('Z','+00:00')) > datetime.fromisoformat(case['now'].replace('Z','+00:00')))
        assert allowed == case['expected_allowed'],case['id']
    for case in cases['mcp_cases']:
        binding=case['binding']; assert not validate('MCPServerBinding',binding)
        allowed=(binding['enabled'] and case['token_resource']==binding['auth_resource'] and
                 all(t['schema_sha256']==case['discovered_schema_hash'] and t['read_only'] for t in binding['allowed_tool_bindings']))
        assert allowed==case['expected_allowed'],case['id']
    for case in cases['skill_cases']:
        skill=case['manifest']; assert not validate('SkillManifest',skill)
        safe_paths=all(not PurePosixPath(x).is_absolute() and '..' not in PurePosixPath(x).parts and '://' not in x for x in [skill['instructions_ref'],*skill['reference_paths']])
        allowed=(skill['status']=='active' and case['role'] in skill['applicable_roles'] and
                 set(skill['required_tool_refs'])<=set(case['granted_tools']) and safe_paths and not skill['scripts_enabled'])
        assert allowed==case['expected_allowed'],case['id']
    policy=load('contracts/agentic-policy.json')
    ctx=policy['context']
    assert ctx['input_budget']==ctx['la01_total_window_budget']-ctx['output_reserve']-ctx['safety_reserve']==3240
    assert policy['status']=='pilot_not_production' and not policy['mcp']['production_enabled']
    assert not policy['skills']['scripts_enabled'] and not policy['observability']['capture_content_by_default']
    assert not policy['observability']['replay_real_side_effects']
    journey=load('contracts/journey-coverage.json')
    stages={stage['stage_id']:stage for stage in journey['stages']}
    assert len(stages)==len(journey['stages'])==11
    for stage in stages.values():
        assert stage['student_visible_state'] and stage['persisted_state'] and stage['owner']
        assert stage['next_stages'] and set(stage['next_stages'])<=set(stages)
        assert stage['exception_exit'] in stages
    def reachable(start):
        seen=set();todo=[start]
        while todo:
            item=todo.pop()
            if item in seen:continue
            seen.add(item);todo.extend(stages[item]['next_stages'])
        return seen
    assert reachable(journey['entry_stage'])==set(stages)
    assert all(journey['completion_stage'] in reachable(stage) for stage in stages)
    for field,prefix,total in [('functional_requirements','LA01-FR',24),('nonfunctional_requirements','LA01-NFR',23),('acceptance_specs','LA01-AT',28)]:
        actual={ref for stage in stages.values() for ref in stage[field]}
        assert actual=={f'{prefix}-{i:02}' for i in range(1,total+1)},(field,actual)
    for label in ['User Journey','Agent Harness','Agentic可观测性','多Agent交互协议与MCP','Skills注册']:
        assert label in text,label
    return {'engineering_schema_definitions':len(engineering_schema['$defs']),
            'engineering_constraint_cases':sum(len(cases[k]) for k in ['valid','invalid','context_cases','memory_cases','mcp_cases','skill_cases']),
            'journey_stages':len(stages),'journey_all_local_requirements_mapped':True}


def check():
    schema = load('contracts/la01.schema.json')
    Draft202012Validator.check_schema(schema)
    upstream_path = ROOT/'docs/design/ai-agent/contracts/learning-agent.schema.json'
    upstream_schema = json.loads(upstream_path.read_text())
    for name in ('InputRefs','Error'):
        assert schema['$defs'][name] == upstream_schema['$defs'][name]
    cases = load('examples/la01-cases.json')
    def validator(name):
        chosen = copy.deepcopy(schema)
        chosen['$ref'] = '#/$defs/' + name
        return Draft202012Validator(chosen, format_checker=FormatChecker())
    for category in ('valid','invalid'):
        for case in cases[category]:
            errors = list(validator(case['definition']).iter_errors(case['value']))
            assert (not errors) == (category == 'valid'), (case['id'], [e.message for e in errors])
    api_path = BASE/'contracts/la01.openapi.json'
    api = json.loads(api_path.read_text())
    OpenAPIV31SpecValidator(api, base_uri=api_path.as_uri()).validate()
    for path, methods in api['paths'].items():
        for method, operation in methods.items():
            assert operation['security']
            if path.startswith('/internal/'):
                assert operation['security'] == [{'workloadBearer':[]}]
            if method == 'post':
                assert any(x['name']=='Idempotency-Key' and x['required'] for x in operation['parameters'])
    catalog = load('contracts/workflow-catalog.json')
    assert len(catalog['templates']) == 3
    for template in catalog['templates']:
        steps = {x['step_id']:x for x in template['steps']}
        assert len(steps) == len(template['steps'])
        done, visiting = set(), set()
        def walk(step):
            assert step in steps and step not in visiting
            if step in done:
                return
            visiting.add(step)
            for parent in steps[step]['depends_on']:
                walk(parent)
            visiting.remove(step)
            done.add(step)
        for step in steps:
            walk(step)
        if template['intent']=='explain_and_replan':
            assert steps['propose_plan']['depends_on'] == ['commit_personal']
            assert steps['propose_plan']['bind_confirmed_personal_from']=='commit_personal'
    for case in cases['gate_cases']:
        validator('CoordinationContext').validate(case['context'])
        validator('IntentProposal').validate(case['proposal'])
        assert gate(case['context'],case['proposal'],catalog) == case['expected_gate'],case['id']
    context = next(x['value'] for x in cases['valid'] if x['definition']=='CoordinationContext')
    for case in cases['plan_cases']:
        validator('CoordinationPlan').validate(case['value'])
        try:
            validate_plan(case['value'],context,catalog)
            valid = True
        except AssertionError:
            valid = False
        assert valid == (case['expected']=='valid'),case['id']
    text = MAIN.read_text()
    for prefix, total in [('LA01-FR',24),('LA01-NFR',23),('LA01-AT',28)]:
        definitions = re.findall(r'^\| ('+prefix+r'-\d{2}) \|',text,re.M)
        assert set(definitions)=={f'{prefix}-{i:02}' for i in range(1,total+1)}
        assert len(definitions)==total
    for label in ('C1 系统上下文','C2 容器','C3 组件','C4 代码'):
        assert label in text
    engineering_result = check_engineering(text)
    req = ROOT/'docs/requirements/通用Agentic学习与考试平台-系统需求规格说明书-v0.3.md'
    pattern = r'\b(?:FR-[A-Z]+|AR|MAC|NFR|IR|UX|AC|T)-\d{2}\b'
    assert set(re.findall(pattern,text)) <= set(re.findall(pattern,req.read_text()))
    for path in [MAIN,*BASE.rglob('*.md')]:
        check_markdown(path)
    backlinks = [PARENT,req,ROOT/'docs/design/学生持续学习-AI-Agent群程序设计与工程脚手架-v1.0.md',ROOT/'docs/architecture/学生持续学习-多Agent与RAG-4A专项架构设计-v1.0.md',ROOT/'docs/architecture/通用Agentic学习与考试平台-4A总体架构设计-v1.1.md']
    for parent in backlinks:
        assert MAIN.name in parent.read_text() and parent.name in text,parent
    # This validates the existing common contract package; not the old rolled-back program backlink.
    common = subprocess.run([sys.executable,str(ROOT/'docs/design/ai-agent/verification/check_design.py')],capture_output=True,text=True,check=True)
    result = json.loads(common.stdout)
    print(json.dumps({**engineering_result,'status':'pass','functional_requirements':24,'nonfunctional_requirements':23,
                      'acceptance_specs_not_executed':28,'c4_levels_present':4,
                      'local_schema_definitions':len(schema['$defs']),'local_openapi_paths':len(api['paths']),
                      'valid_contract_cases':len(cases['valid']),'invalid_contract_cases_rejected':len(cases['invalid']),
                      'synthetic_gate_cases':len(cases['gate_cases']),'compiled_plan_cases':len(cases['plan_cases']),
                      'workflow_templates':len(catalog['templates']), 'upstream_contract_status':result['status'],
                      'archive_files_unchanged':result['archive_files_unchanged'],
                      'real_model_or_services_tested':False,'mermaid_rendered':False},ensure_ascii=False,indent=2))


if __name__=='__main__':
    check()
