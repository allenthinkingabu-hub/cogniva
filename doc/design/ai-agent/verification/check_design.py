"""Validate design artifacts only. Does not start services or call external models.
Requires: jsonschema, PyYAML, openapi-spec-validator in an isolated tool environment.
Run: python check_design.py
"""
from pathlib import Path
import copy
import json
import re
import hashlib
from urllib.parse import unquote
import yaml
from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import OpenAPIV31SpecValidator

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[2]
MAIN = BASE.parent / '学生持续学习-AI-Agent群详细设计-v1.0.md'
ARCH = ROOT / 'docs/architecture/学生持续学习-多Agent与RAG-4A专项架构设计-v1.0.md'
TOP = ROOT / 'docs/architecture/通用Agentic学习与考试平台-4A总体架构设计-v1.1.md'


def read_json(relative):
    return json.loads((BASE / relative).read_text())


def check():
    schema = read_json('contracts/learning-agent.schema.json')
    Draft202012Validator.check_schema(schema)
    cases = read_json('examples/contract-cases.json')
    for category in ('valid', 'invalid'):
        for case in cases[category]:
            selected = copy.deepcopy(schema)
            selected['$ref'] = '#/$defs/' + case['definition']
            validator = Draft202012Validator(selected, format_checker=FormatChecker())
            errors = list(validator.iter_errors(case['value']))
            assert (not errors) == (category == 'valid'), (case['id'], [e.message for e in errors])
    api_path = BASE / 'contracts/learning-agent.openapi.json'
    api = json.loads(api_path.read_text())
    OpenAPIV31SpecValidator(api, base_uri=api_path.as_uri()).validate()
    for methods in api['paths'].values():
        for method, op in methods.items():
            assert method in ('get', 'post')
            assert op['security'] and op['operationId']
            assert all(status in op['responses'] for status in ('400', '401', '403', '409', '422', '429', '503'))
    # All new Markdown attachments use relative links resolved against their own directories.
    for markdown in BASE.rglob('*.md'):
        plain_attachment = re.sub(r'```.*?```', '', markdown.read_text(), flags=re.S)
        for target in re.findall(r'\]\(([^)]+)\)', plain_attachment):
            if '://' in target or target.startswith('#'):
                continue
            assert (markdown.parent / unquote(target.split('#')[0])).exists(), (markdown, target)
    text = MAIN.read_text()
    assert text.count('```') % 2 == 0
    # Read only new Markdown plus its new links; historical incomplete architecture links are out of scope.
    plain = re.sub(r'```.*?```', '', text, flags=re.S)
    for target in re.findall(r'\]\(([^)]+)\)', plain):
        if '://' in target or target.startswith('#'):
            continue
        assert (MAIN.parent / unquote(target.split('#')[0])).exists(), target
    previous = None
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith('|'):
            count = line.count('|')
            if previous and previous[0] + 1 == number:
                assert previous[1] == count, ('table column mismatch', number)
            previous = (number, count)
    assert MAIN.name in ARCH.read_text() and ARCH.name in text
    assert MAIN.name in TOP.read_text() and TOP.name in text
    req = ROOT / 'docs/requirements/通用Agentic学习与考试平台-系统需求规格说明书-v0.3.md'
    known = set(re.findall(r'\b(?:FR-[A-Z]+|AR|MAC|NFR|IR|UX|AC|T)-\d{2}\b', req.read_text()))
    used = set(re.findall(r'\b(?:FR-[A-Z]+|AR|MAC|NFR|IR|UX|AC|T)-\d{2}\b', text))
    assert used <= known, sorted(used - known)
    manifests = list((ROOT / 'docs/architecture/archive').glob('*/manifest.json'))
    archived = 0
    for manifest in manifests:
        for item in json.loads(manifest.read_text())['files']:
            file = manifest.parent / item['path']
            assert hashlib.sha256(file.read_bytes()).hexdigest() == item['sha256'], file
            archived += 1
    deployment = list(yaml.safe_load_all((BASE / 'deployment/agent-worker.example.yaml').read_text()))
    assert [x['kind'] for x in deployment] == ['ServiceAccount', 'Deployment', 'PodDisruptionBudget']
    pod = deployment[1]['spec']['template']['spec']
    assert pod['securityContext']['runAsNonRoot']
    assert not pod['automountServiceAccountToken']
    assert all(k in pod['containers'][0] for k in ('startupProbe', 'readinessProbe', 'livenessProbe', 'resources'))
    policy = read_json('deployment/pilot-policy.json')
    assert policy['status'] == 'pilot_not_production' and policy['requires_approval_before_production']
    assert set(policy['roles']) == {'LA-01', 'LA-02', 'LA-03', 'LA-04', 'LA-05'}
    print(json.dumps({'status':'pass','schema_definitions':len(schema['$defs']),
                      'openapi_paths':len(api['paths']), 'valid_cases':len(cases['valid']),
                      'rejected_cases':len(cases['invalid']), 'archive_files_unchanged':archived,
                      'checks':['JSON Schema','OpenAPI validation and references','synthetic cases',
                                'Markdown new links/tables/fences','bidirectional links',
                                'requirement identifiers','archive hashes','YAML parse/template assertions','pilot config'],
                      'not_verified':['deployed services','model/teaching quality','runtime authorization',
                                      'Kubernetes server validation','Mermaid rendering','load/HA/security/recovery']},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    check()
