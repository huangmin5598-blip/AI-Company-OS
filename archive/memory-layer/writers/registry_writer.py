#!/usr/bin/env python3
"""
Registry Writer - Generic Unified Registry Writer

Pure write layer that writes to Asset Registry, Execution Records, and Project Registry.
Does NOT handle business logic, content analysis, or project-specific branches.

Usage:
    python registry_writer.py --input processed_asset_bundle.json
    python registry_writer.py --asset_id xxx --project_id xxx --type novel ...
"""

import json
import argparse
import os
from datetime import datetime
from typing import Dict, Any, List, Optional


# Registry file paths
ASSET_REGISTRY_PATH = "/Users/tangbomao/.openclaw/workspace/memory-layer/registry/asset-registry.yaml"
EXECUTION_REGISTRY_PATH = "/Users/tangbomao/.openclaw/workspace/memory-layer/registry/execution-records.yaml"
PROJECT_REGISTRY_PATH = "/Users/tangbomao/.openclaw/workspace/memory-layer/registry/project-registry.yaml"


def ensure_registry_dir():
    """Ensure registry directory exists"""
    os.makedirs(os.path.dirname(ASSET_REGISTRY_PATH), exist_ok=True)


def load_yaml_registry(file_path: str) -> Dict[str, Any]:
    """Load YAML registry (simulated as JSON for now)"""
    json_path = file_path.replace('.yaml', '.json')
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)
    return {}


def save_yaml_registry(file_path: str, data: Dict[str, Any]):
    """Save registry (as JSON for simplicity)"""
    ensure_registry_dir()
    json_path = file_path.replace('.yaml', '.json')
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_asset_record(asset_record: Dict[str, Any]) -> bool:
    """Write asset record to Asset Registry"""
    registry = load_yaml_registry(ASSET_REGISTRY_PATH)
    
    # Ensure assets key exists
    if "assets" not in registry:
        registry["assets"] = []
    
    # Check if asset already exists (update) or new (append)
    existing_index = None
    for i, existing in enumerate(registry.get("assets", [])):
        if existing.get("asset_id") == asset_record.get("asset_id"):
            existing_index = i
            break
    
    if existing_index is not None:
        registry["assets"][existing_index] = asset_record
    else:
        registry["assets"].append(asset_record)
    
    save_yaml_registry(ASSET_REGISTRY_PATH, registry)
    return True


def write_execution_record(execution_record: Dict[str, Any]) -> bool:
    """Write execution record to Execution Records Registry"""
    registry = load_yaml_registry(EXECUTION_REGISTRY_PATH)
    
    if "records" not in registry:
        registry["records"] = []
    
    # Append new record
    registry["records"].append(execution_record)
    
    save_yaml_registry(EXECUTION_REGISTRY_PATH, registry)
    return True


def update_project_registry(project_update: Dict[str, Any]) -> bool:
    """Update Project Registry with latest completed task"""
    registry = load_yaml_registry(PROJECT_REGISTRY_PATH)
    
    if "projects" not in registry:
        registry["projects"] = []
    
    project_id = project_update.get("project_id")
    
    # Find and update project
    existing_index = None
    for i, existing in enumerate(registry.get("projects", [])):
        if existing.get("project_id") == project_id:
            existing_index = i
            break
    
    if existing_index is not None:
        # Update existing project
        registry["projects"][existing_index].update({
            "last_updated_at": project_update.get("last_updated_at"),
            "last_completed_task": project_update.get("last_completed_task"),
            "status": project_update.get("status", "ACTIVE")
        })
    else:
        # Create new project entry
        registry["projects"].append({
            "project_id": project_id,
            "last_updated_at": project_update.get("last_updated_at"),
            "last_completed_task": project_update.get("last_completed_task"),
            "related_assets_add": project_update.get("related_assets_add", []),
            "status": project_update.get("status", "ACTIVE"),
            "created_at": datetime.now().isoformat()
        })
    
    save_yaml_registry(PROJECT_REGISTRY_PATH, registry)
    return True


def write_knowledge_candidate(knowledge_candidate: Dict[str, Any]) -> bool:
    """Write knowledge candidate to Knowledge Registry (optional)"""
    if not knowledge_candidate:
        return True
    
    knowledge_path = "/Users/tangbomao/.openclaw/workspace/memory-layer/registry/knowledge-registry.json"
    ensure_registry_dir()
    
    registry = load_yaml_registry(knowledge_path)
    
    if "candidates" not in registry:
        registry["candidates"] = []
    
    registry["candidates"].append(knowledge_candidate)
    
    save_yaml_registry(knowledge_path, registry)
    return True


def process_input(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process input bundle and write to registries"""
    
    results = {
        "asset_record": None,
        "execution_record": None,
        "project_update": None,
        "knowledge_candidate": None,
        "status": "success"
    }
    
    # Write asset record
    if input_data.get("asset_record"):
        success = write_asset_record(input_data["asset_record"])
        results["asset_record"] = "written" if success else "failed"
    
    # Write execution record
    if input_data.get("execution_record"):
        success = write_execution_record(input_data["execution_record"])
        results["execution_record"] = "written" if success else "failed"
    
    # Update project registry
    if input_data.get("project_update"):
        success = update_project_registry(input_data["project_update"])
        results["project_update"] = "updated" if success else "failed"
    
    # Write knowledge candidate
    if input_data.get("knowledge_candidate"):
        success = write_knowledge_candidate(input_data["knowledge_candidate"])
        results["knowledge_candidate"] = "written" if success else "failed"
    
    results["processed_at"] = datetime.now().isoformat()
    
    return results


def load_input_from_file(file_path: str) -> Dict[str, Any]:
    """Load input bundle from JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Registry Writer - Generic Unified Registry")
    parser.add_argument("--input", type=str, help="Path to processed_asset_bundle.json")
    parser.add_argument("--asset_id", type=str, help="Asset ID")
    parser.add_argument("--project_id", type=str, help="Project ID")
    parser.add_argument("--dry_run", action="store_true", help="Dry run (don't actually write)")
    
    args = parser.parse_args()
    
    if args.input:
        # Load from file
        input_data = load_input_from_file(args.input)
    else:
        print("Error: --input is required")
        return
    
    if args.dry_run:
        print("[DRY RUN] Would process:")
        print(json.dumps(input_data, indent=2, ensure_ascii=False))
        return
    
    # Process and write
    results = process_input(input_data)
    
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
