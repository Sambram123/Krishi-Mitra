---
phase: 1
plan: 1
wave: 1
---

# Plan 1.1: Reference Dataset & Deterministic Rule Engine

## Objective
Model the hackathon reference dataset (PM-KISAN, PMFBY, Demo Micro-Irrigation, Demo Agri Equipment, Demo Soil Improvement) into structured JSON and build the deterministic, zero-hallucination Python rule engine with complete test coverage.

## Context
- .gsd/SPEC.md
- .gsd/ROADMAP.md
- dataset_research.md
- schemes_knowledge_base.md

## Tasks

<task type="auto">
  <name>Create Reference Schemes Dataset Schema</name>
  <files>data/schemes_dataset.json</files>
  <action>
    Create data/schemes_dataset.json containing the 5 benchmark schemes:
    - 2 Real schemes: PM-KISAN, PMFBY (with official exclusions, documents, Kannada text).
    - 3 Synthetic schemes: Demo Micro-Irrigation, Demo Agricultural Equipment, Demo Soil Improvement.
    Include eligibility rules, condition thresholds, and Kannada metadata.
  </action>
  <verify>python -c "import json; data=json.load(open('data/schemes_dataset.json', encoding='utf-8')); assert len(data['schemes']) == 5; print('Dataset verified')"</verify>
  <done>data/schemes_dataset.json exists, valid JSON, contains all 5 schemes with required metadata</done>
</task>

<task type="auto">
  <name>Build Deterministic Scheme Rule Engine</name>
  <files>backend/rules_engine.py</files>
  <action>
    Implement rules_engine.py in Python:
    - Define FarmerProfile and EvaluationResult data classes.
    - Implement deterministic evaluation functions for all 5 schemes.
    - Generate human-readable Kannada & English audit trails detailing why a farmer qualifies or is excluded.
    - Attach mandatory and optional document checklists for qualified schemes.
  </action>
  <verify>python -c "from backend.rules_engine import SchemeEvaluator; print('Evaluator imported successfully')"</verify>
  <done>backend/rules_engine.py cleanly evaluates profiles and returns structured audit results</done>
</task>

<task type="auto">
  <name>Implement Automated Rule Engine Test Suite</name>
  <files>backend/test_rules.py</files>
  <action>
    Write comprehensive unit tests in backend/test_rules.py:
    - Test PM-KISAN positive and exclusion cases (taxpayer exclusion).
    - Test PMFBY crop loss and season match.
    - Test Demo Micro-Irrigation (90% small farmer vs 70% large farmer vs water source missing).
    - Test Demo Agricultural Equipment Assistance subsidy caps.
    - Test Demo Soil Improvement Support with soil deficiency.
  </action>
  <verify>python -m unittest backend/test_rules.py -v</verify>
  <done>All unit tests pass with zero failures and zero errors</done>
</task>

## Success Criteria
- [ ] data/schemes_dataset.json cleanly models all 5 schemes.
- [ ] backend/rules_engine.py delivers deterministic, zero-hallucination results with audit trails.
- [ ] 100% of unit tests pass in backend/test_rules.py.
