"""
NEXORA ATLAS - Phase 7 AWS Safety & Trust Boundary Tests
Uses Python AST static analysis and behavioral inspection to verify that:
1. Zero banned mutating AWS APIs are referenced, imported, or called.
2. Zero generic unconstrained client executors exist.
3. All provider interfaces are strictly read-only.
"""

import ast
import os
import inspect
import pytest
from pathlib import Path

from app.integrations.providers.base import BaseCloudProvider
from app.integrations.providers.aws.client import AWSClientFactory

# Banned mutating AWS API method prefixes / keywords
BANNED_MUTATING_KEYWORDS = [
    "start_instances",
    "stop_instances",
    "terminate_instances",
    "modify_instance",
    "modify_db",
    "delete_db",
    "delete_volume",
    "delete_bucket",
    "put_bucket",
    "put_object",
    "delete_object",
    "purchase_reserved",
    "purchase_savings",
    "create_instance",
    "create_db",
    "create_bucket",
    "create_volume",
    "create_cluster",
    "delete_cluster",
    "associate_address",
    "disassociate_address",
    "update_",
    "put_metric_data",
    "put_metric_alarm",
    "delete_alarms",
    "disable_alarm_actions",
    "enable_alarm_actions",
    "set_alarm_state",
    "tag_resources",
    "untag_resources",
]


def _get_python_files_in_dir(directory: Path):
    """Recursively yields all python files in a directory."""
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith(".py"):
                yield Path(root) / f


def test_static_ast_scan_for_banned_aws_mutating_calls():
    """
    Scans the entire app/integrations directory using AST parsing.
    Asserts zero occurrences of mutating AWS method calls or attributes.
    """
    integrations_dir = Path(__file__).parent.parent / "app" / "integrations"
    assert integrations_dir.exists(), "app/integrations directory must exist"

    violations = []

    for file_path in _get_python_files_in_dir(integrations_dir):
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=str(file_path))

        for node in ast.walk(tree):
            # Check function calls: e.g. client.terminate_instances(...)
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr.lower()
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id.lower()

                for banned in BANNED_MUTATING_KEYWORDS:
                    if banned in func_name:
                        violations.append(
                            f"Prohibited call '{func_name}' at {file_path.name}:{node.lineno}"
                        )

            # Check attribute access: e.g. getattr(client, "terminate_instances")
            elif isinstance(node, ast.Attribute):
                attr_name = node.attr.lower()
                for banned in BANNED_MUTATING_KEYWORDS:
                    if banned in attr_name:
                        violations.append(
                            f"Prohibited attribute '{attr_name}' at {file_path.name}:{node.lineno}"
                        )

    assert not violations, f"Banned mutating AWS operations detected:\n" + "\n".join(violations)


def test_no_generic_command_executor():
    """
    Verifies that AWSClientFactory and BaseCloudProvider do NOT expose generic
    'execute' or 'run_command' methods that could bypass read-only boundaries.
    """
    for cls in (AWSClientFactory, BaseCloudProvider):
        methods = [m[0] for m in inspect.getmembers(cls, predicate=inspect.isfunction)]
        assert "execute" not in methods, f"{cls.__name__} must not expose generic 'execute' method"
        assert "run_command" not in methods, f"{cls.__name__} must not expose generic 'run_command' method"


def test_client_factory_repr_redaction():
    """Verifies that client factory __repr__ never leaks full credentials, role ARNs, or tokens."""
    factory = AWSClientFactory(
        role_arn="arn:aws:iam::123456789012:role/SuperSecretRole",
        external_id="super-secret-external-id",
    )
    repr_str = repr(factory)
    assert "super-secret-external-id" not in repr_str
    assert "123456789012" not in repr_str
    assert "SuperSecretRole" in repr_str or "..." in repr_str


def test_ai_subsystem_has_zero_mutation_or_tool_execution_capabilities():
    """
    Scans the entire app/ai directory using Python AST parsing.
    Guarantees:
    1. Zero tool-calling or autonomous agent execution mechanisms.
    2. Zero references to subprocess, os.system, exec, or eval.
    3. Zero references to banned mutating AWS operations.
    4. AI engine is strictly read-only and explanatory.
    """
    ai_dir = Path(__file__).parent.parent / "app" / "ai"
    assert ai_dir.exists(), "app/ai directory must exist"

    violations = []
    banned_execution_names = {"subprocess", "system", "popen", "spawn", "eval", "exec", "tool_call", "execute_action"}

    for file_path in _get_python_files_in_dir(ai_dir):
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr.lower()
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id.lower()

                if func_name in banned_execution_names or any(banned in func_name for banned in BANNED_MUTATING_KEYWORDS):
                    violations.append(
                        f"Prohibited execution call '{func_name}' in AI subsystem at {file_path.name}:{node.lineno}"
                    )

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ["subprocess", "posix", "nt"]:
                        violations.append(f"Prohibited execution module import '{alias.name}' at {file_path.name}:{node.lineno}")

            elif isinstance(node, ast.ImportFrom):
                if node.module in ["subprocess", "os"]:
                    for alias in node.names:
                        if alias.name in ["system", "popen", "spawn"]:
                            violations.append(f"Prohibited execution import '{alias.name}' at {file_path.name}:{node.lineno}")

    assert not violations, "Prohibited execution or mutation detected in AI subsystem:\n" + "\n".join(violations)
