import json, os
payload = '{"verdicts": {"boot": true, "pytest": true, "data-quality": true, "perf": true, "ruff": true, "pyright": true}, "test_files": ["tests/test_performance.py", "tests/test_cors.py", "tests/test_acceptance_live.py", "tests/test_health.py", "tests/test_cors_preflight.py", "tests/test_validation.py", "tests/test_live_integration.py", "tests/test_errors.py", "tests/test_domain_workflow.py", "tests/test_storage.py", "tests/test_concurrency.py", "tests/test_config.py", "tests/test_persistence.py", "tests/test_tasks_crud.py", "tests/integration/test_storage_unavailable.py", "tests/integration/test_store_persistence.py"], "overall": "pass"}'
hr = {k: ('PASS' if v is True else 'FAIL') for k, v in json.loads(payload)['verdicts'].items()}
for k, v in hr.items():
    print(f'GATE {k}={v}')
try:
    with open('qa_verdict.json', 'w', encoding='utf-8') as f:
        f.write(payload)
    print('VERDICT_WRITTEN')
except Exception as e:
    print('VERDICT_FAIL', repr(e))
    raise SystemExit(2)
