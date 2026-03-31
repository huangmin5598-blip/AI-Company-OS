#!/usr/bin/env python3
"""
Asset Processor - Generic Asset Standardization Layer

Receives task_completed_event and converts to standardized asset structures
for Registry Writer.

Usage:
    python asset_processor.py --event task_completed_event.json
    python asset_processor.py --project novel-v1 --task novel-17 --type novel ...
"""

import json
import argparse
import os
from datetime import datetime
from typing import Dict, Any, Optional


def generate_asset_id(project_id: str, task_id: str) -> str:
    """Generate unique asset ID"""
    return f"{project_id}-{task_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def generate_record_id(project_id: str, task_id: str) -> str:
    """Generate unique execution record ID"""
    return f"exec-{project_id}-{task_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def process_novel_metadata(metadata: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """Process novel-specific metadata"""
    return {
        "genre": metadata.get("genre", "unknown"),
        "scene_count": metadata.get("scene_count", 0),
        "word_count": metadata.get("word_count", 0),
        "review_pass": metadata.get("review_pass", True),
        "chapters": metadata.get("chapters", [])
    }


def process_article_metadata(metadata: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """Process article-specific metadata"""
    return {
        "platform": metadata.get("platform", "unknown"),
        "topic": metadata.get("topic", ""),
        "audience": metadata.get("audience", ""),
        "seo_keywords": metadata.get("seo_keywords", [])
    }


def process_image_metadata(metadata: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """Process image-specific metadata"""
    return {
        "prompt_ref": metadata.get("prompt_ref", ""),
        "size": metadata.get("size", ""),
        "style": metadata.get("style", "")
    }


def process_video_script_metadata(metadata: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """Process video_script-specific metadata"""
    return {
        "duration": metadata.get("duration", 0),
        "platform": metadata.get("platform", ""),
        "shot_count": metadata.get("shot_count", 0),
        "thumbnail_ref": metadata.get("thumbnail_ref", "")
    }


def process_social_post_metadata(metadata: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """Process social_post-specific metadata"""
    return {
        "platform": metadata.get("platform", ""),
        "character_count": metadata.get("character_count", 0),
        "hashtag_count": metadata.get("hashtag_count", 0)
    }


def process_document_metadata(metadata: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """Process document-specific metadata"""
    return {
        "file_format": metadata.get("file_format", "unknown"),
        "use_case": metadata.get("use_case", ""),
        "page_count": metadata.get("page_count", 0)
    }


def process_report_metadata(metadata: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """Process report-specific metadata"""
    return {
        "report_type": metadata.get("report_type", "unknown"),
        "period": metadata.get("period", ""),
        "stakeholders": metadata.get("stakeholders", [])
    }


def process_prd_metadata(metadata: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """Process prd-specific metadata"""
    return {
        "product_name": metadata.get("product_name", ""),
        "stage": metadata.get("stage", "idea"),
        "version": metadata.get("version", "1.0"),
        "target_users": metadata.get("target_users", [])
    }


def process_protocol_metadata(metadata: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """Process protocol-specific metadata"""
    return {
        "protocol_name": metadata.get("protocol_name", ""),
        "version": metadata.get("version", "1.0"),
        "scope": metadata.get("scope", ""),
        "dependencies": metadata.get("dependencies", [])
    }


def process_workflow_metadata(metadata: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """Process workflow-specific metadata"""
    return {
        "workflow_name": metadata.get("workflow_name", ""),
        "trigger": metadata.get("trigger", ""),
        "steps": metadata.get("steps", []),
        "automated": metadata.get("automated", False)
    }


def process_prompt_template_metadata(metadata: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """Process prompt_template-specific metadata"""
    return {
        "template_name": metadata.get("template_name", ""),
        "model": metadata.get("model", ""),
        "use_case": metadata.get("use_case", ""),
        "variables": metadata.get("variables", [])
    }


def process_code_metadata(metadata: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """Process code-specific metadata"""
    return {
        "language": metadata.get("language", "unknown"),
        "module": metadata.get("module", ""),
        "framework": metadata.get("framework", ""),
        "functions": metadata.get("functions", [])
    }


# Asset type to processor mapping
METADATA_PROCESSORS = {
    "novel": process_novel_metadata,
    "article": process_article_metadata,
    "image": process_image_metadata,
    "video_script": process_video_script_metadata,
    "social_post": process_social_post_metadata,
    "document": process_document_metadata,
    "report": process_report_metadata,
    "prd": process_prd_metadata,
    "protocol": process_protocol_metadata,
    "workflow": process_workflow_metadata,
    "prompt_template": process_prompt_template_metadata,
    "code": process_code_metadata,
    "markdown": lambda m, e: {},
    "docx": lambda m, e: {}
}


def process_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Process task_completed_event and generate standardized output"""

    project_id = event.get("project_id", "")
    task_id = event.get("task_id", "")
    asset_type = event.get("asset_type", "unknown")
    completed_at = event.get("completed_at", datetime.now().isoformat())
    metadata = event.get("metadata", {})

    # Generate IDs
    asset_id = generate_asset_id(project_id, task_id)
    record_id = generate_record_id(project_id, task_id)

    # Process metadata based on asset_type
    processor = METADATA_PROCESSORS.get(asset_type, lambda m, e: {})
    processed_metadata = processor(metadata, event)

    # Build asset_record
    asset_record = {
        "asset_id": asset_id,
        "project_id": project_id,
        "asset_type": asset_type,
        "title": event.get("title", ""),
        "summary": event.get("summary", ""),
        "status": event.get("status", "ready"),
        "version": "1.0",
        "created_by": event.get("created_by", "unknown"),
        "source_task": task_id,
        "review_status": event.get("review_status", "PASS"),
        "copyright_status": event.get("copyright_status", "LOW"),
        "publish_status": event.get("publish_status", "ready"),
        "file_path": event.get("output_path", ""),
        "tags": metadata.get("tags", []),
        "created_at": completed_at,
        "updated_at": completed_at,
        "metadata": processed_metadata
    }

    # Build execution_record
    execution_record = {
        "record_id": record_id,
        "task_id": task_id,
        "project_id": project_id,
        "agent_chain": metadata.get("agent_chain", []),
        "timeout_count": metadata.get("timeout_count", 0),
        "fallback_history": metadata.get("fallback_history", []),
        "degradation_flag": metadata.get("degradation_flag", False),
        "final_output_path": event.get("output_path", ""),
        "result": event.get("review_status", "PASS"),
        "completed_at": completed_at
    }

    # Build project_update
    project_update = {
        "project_id": project_id,
        "last_updated_at": completed_at,
        "last_completed_task": task_id,
        "related_assets_add": [asset_id],
        "status": "ACTIVE"
    }

    # Build knowledge_candidate (optional, for future)
    knowledge_candidate = None
    if metadata.get("generate_knowledge_candidate", False):
        knowledge_candidate = {
            "card_id": f"kc-{task_id}",
            "card_type": "pattern",
            "title": f"{asset_type} pattern: {task_id}",
            "summary": event.get("summary", ""),
            "source_project": project_id,
            "applies_to": [project_id],
            "key_rules": [],
            "example_refs": [task_id],
            "tags": [asset_type],
            "created_at": completed_at
        }

    return {
        "asset_record": asset_record,
        "execution_record": execution_record,
        "project_update": project_update,
        "knowledge_candidate": knowledge_candidate,
        "processed_at": datetime.now().isoformat()
    }


def load_event_from_file(file_path: str) -> Dict[str, Any]:
    """Load event from JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)


def save_output(output: Dict[str, Any], output_path: str):
    """Save processed output to file"""
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Asset Processor - Generic Asset Standardization")
    parser.add_argument("--event", type=str, help="Path to task_completed_event.json file")
    parser.add_argument("--project", type=str, help="Project ID")
    parser.add_argument("--task", type=str, help="Task ID")
    parser.add_argument("--type", type=str, help="Asset type (novel/article/image/video_script)")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--title", type=str, help="Asset title")
    parser.add_argument("--summary", type=str, help="Asset summary")
    parser.add_argument("--format", type=str, help="Output format (md/docx/png/etc)")
    parser.add_argument("--path", type=str, help="Output file path")
    parser.add_argument("--metadata", type=str, help="JSON string of metadata")
    
    args = parser.parse_args()
    
    if args.event:
        # Load from file
        event = load_event_from_file(args.event)
    else:
        # Build from CLI args
        metadata = {}
        if args.metadata:
            metadata = json.loads(args.metadata)
        
        event = {
            "event_type": "task_completed",
            "project_id": args.project or "",
            "task_id": args.task or "",
            "task_type": args.type or "unknown",
            "asset_type": args.type or "unknown",
            "status": "completed",
            "output_path": args.path or "",
            "output_format": args.format or "",
            "title": args.title or "",
            "summary": args.summary or "",
            "metadata": metadata,
            "review_status": "PASS",
            "copyright_status": "LOW",
            "publish_status": "ready",
            "created_by": "system",
            "completed_at": datetime.now().isoformat()
        }
    
    # Process
    output = process_event(event)
    
    # Save or print
    if args.output:
        save_output(output, args.output)
        print(f"Processed output saved to: {args.output}")
    else:
        print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
