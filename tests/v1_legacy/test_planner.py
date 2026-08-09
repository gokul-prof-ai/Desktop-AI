"""
DesktopAI
Tests for the AI Planner module.
"""

import ai.classifier as classifier_module
import ai.recommender as recommender_module
import ai.planner as planner_module
from ai.planner import AIPlan


def test_create_plan_returns_five_steps(tmp_path):
    planner = AIPlan()
    plan = planner.create_plan(tmp_path, goal="Organise Downloads")
    assert len(plan.steps) == 5
    assert [s.name for s in plan.steps] == ["scan","classify","recommend","save","explain"]
    assert all(s.status == "pending" for s in plan.steps)


def test_create_plan_stores_goal_and_folder(tmp_path):
    planner = AIPlan()
    plan = planner.create_plan(tmp_path, goal="Tidy my files")
    assert plan.goal == "Tidy my files"
    assert plan.folder == tmp_path


def test_execute_completes_all_steps_with_files(tmp_path, monkeypatch):
    (tmp_path / "invoice.txt").write_text("Invoice total due $500")
    monkeypatch.setattr(classifier_module, "generate_response", lambda p: "Invoice")
    monkeypatch.setattr(recommender_module, "generate_response", lambda p: "Documents/Invoices")
    monkeypatch.setattr(planner_module, "generate_response", lambda p: "Found 1 invoice.")

    planner = AIPlan()
    plan = planner.create_plan(tmp_path)
    planner.execute(plan)

    statuses = {s.name: s.status for s in plan.steps}
    assert all(v == "completed" for v in statuses.values())


def test_execute_produces_organisation_actions(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("Invoice total due $500")
    (tmp_path / "b.txt").write_text("Resume experience engineer")
    monkeypatch.setattr(classifier_module, "generate_response", lambda p: "Invoice")
    monkeypatch.setattr(recommender_module, "generate_response", lambda p: "Documents/Sorted")
    monkeypatch.setattr(planner_module, "generate_response", lambda p: "Done.")

    planner = AIPlan()
    plan = planner.create_plan(tmp_path)
    planner.execute(plan)

    assert len(plan.actions) == 2
    assert all(a.status == "pending" for a in plan.actions)


def test_execute_skips_classify_and_recommend_on_empty_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(planner_module, "generate_response", lambda p: "Nothing found.")
    planner = AIPlan()
    plan = planner.create_plan(tmp_path)
    planner.execute(plan)
    statuses = {s.name: s.status for s in plan.steps}
    assert statuses["classify"] == "skipped"
    assert statuses["recommend"] == "skipped"
    assert statuses["scan"] == "completed"


def test_execute_uses_fallback_summary_when_ai_unavailable(tmp_path, monkeypatch):
    (tmp_path / "notes.txt").write_text("Meeting notes Q3")
    monkeypatch.setattr(classifier_module, "generate_response", lambda p: None)
    monkeypatch.setattr(recommender_module, "generate_response", lambda p: None)
    monkeypatch.setattr(planner_module, "generate_response", lambda p: None)

    planner = AIPlan()
    plan = planner.create_plan(tmp_path)
    planner.execute(plan)

    explain_step = next(s for s in plan.steps if s.name == "explain")
    assert explain_step.status == "completed"
    assert plan.summary != ""


def test_plan_actions_are_not_applied_by_planner(tmp_path, monkeypatch):
    file1 = tmp_path / "doc.txt"
    file1.write_text("Some document content")
    monkeypatch.setattr(classifier_module, "generate_response", lambda p: "Document")
    monkeypatch.setattr(recommender_module, "generate_response", lambda p: "Documents/General")
    monkeypatch.setattr(planner_module, "generate_response", lambda p: "Summary.")

    planner = AIPlan()
    plan = planner.create_plan(tmp_path)
    planner.execute(plan)

    assert file1.exists(), "Planner must not move files without user approval"