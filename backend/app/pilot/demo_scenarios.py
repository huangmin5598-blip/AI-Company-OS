"""Deterministic multi-offer demo scenarios for the local pilot workbench."""

from __future__ import annotations

from dataclasses import dataclass


PILOT_AUTHORITY = "pilot_non_authoritative"
DEMO_MODE = "demo_spine_pilot"
DEMO_SOURCE_PATH = "founder_control_center_demo_spine"


@dataclass(frozen=True)
class DemoTaskTemplate:
    title: str
    executor_slot: str
    expected_output: str
    audit_summary: str


@dataclass(frozen=True)
class DemoOffer:
    offer_id: str
    display_name: str
    tagline: str
    default_goal: str
    final_asset_title: str
    final_asset_template: str
    tasks: tuple[DemoTaskTemplate, ...]


OFFERS: tuple[DemoOffer, ...] = (
    DemoOffer(
        offer_id="idea_to_prd_pilot",
        display_name="Idea-to-PRD Pilot",
        tagline="Turn a rough product idea into a validation-ready PRD.",
        default_goal=(
            "Turn my rough AI product idea into a concise PRD and validation plan."
        ),
        final_asset_title="PRD Draft and Validation Checklist",
        final_asset_template=(
            "# Idea-to-PRD Pilot Asset\n\n"
            "Founder goal: {goal}\n\n"
            "## Output\n"
            "- Target user and pain clarified.\n"
            "- Core workflow drafted as a PRD skeleton.\n"
            "- Validation checklist prepared for Founder Go / No-Go.\n"
        ),
        tasks=(
            DemoTaskTemplate(
                title="Clarify target user and painful moment",
                executor_slot="ceo_agent_slot",
                expected_output="User, pain, trigger, and success criteria.",
                audit_summary="CEO Agent framed the PRD discovery scope.",
            ),
            DemoTaskTemplate(
                title="Draft MVP workflow and acceptance criteria",
                executor_slot="codex_slot",
                expected_output="MVP workflow, scope boundaries, acceptance tests.",
                audit_summary="Codex slot produced a structured PRD draft.",
            ),
            DemoTaskTemplate(
                title="Review risks and founder decision questions",
                executor_slot="claude_slot",
                expected_output="Risks, contradictions, and decision prompts.",
                audit_summary="Claude slot reviewed the draft for decision quality.",
            ),
            DemoTaskTemplate(
                title="Assemble validation checklist asset",
                executor_slot="local_script_slot",
                expected_output="Markdown checklist for founder validation.",
                audit_summary="Local script slot assembled the pilot asset.",
            ),
        ),
    ),
    DemoOffer(
        offer_id="spoken_agent_offer",
        display_name="Spoken Agent Offer",
        tagline="Shape a voice-script agent offer into a sellable pilot.",
        default_goal=(
            "Package a voice-script assistant that can produce short sales scripts."
        ),
        final_asset_title="Spoken Agent Offer Brief",
        final_asset_template=(
            "# Spoken Agent Offer Asset\n\n"
            "Founder goal: {goal}\n\n"
            "## Output\n"
            "- Offer promise and audience defined.\n"
            "- Script-generation workflow outlined.\n"
            "- Demo script and review checklist prepared.\n"
        ),
        tasks=(
            DemoTaskTemplate(
                title="Define buyer, use case, and promise",
                executor_slot="ceo_agent_slot",
                expected_output="Buyer profile, job-to-be-done, outcome promise.",
                audit_summary="CEO Agent scoped the voice offer.",
            ),
            DemoTaskTemplate(
                title="Draft short-form script workflow",
                executor_slot="codex_slot",
                expected_output="Prompt structure and review steps.",
                audit_summary="Codex slot drafted the operating workflow.",
            ),
            DemoTaskTemplate(
                title="Create sample spoken script",
                executor_slot="claude_slot",
                expected_output="One reviewable sample script.",
                audit_summary="Claude slot generated a sample script asset.",
            ),
            DemoTaskTemplate(
                title="Prepare Go / No-Go scorecard",
                executor_slot="local_script_slot",
                expected_output="Founder scorecard for pilot readiness.",
                audit_summary="Local script slot assembled the scorecard.",
            ),
        ),
    ),
    DemoOffer(
        offer_id="clip_matrix_agent",
        display_name="Clip Matrix Agent",
        tagline="Plan a repeatable short-video remix workflow.",
        default_goal=(
            "Design a remix matrix assistant for turning source footage into clips."
        ),
        final_asset_title="Clip Matrix Workflow Brief",
        final_asset_template=(
            "# Clip Matrix Agent Asset\n\n"
            "Founder goal: {goal}\n\n"
            "## Output\n"
            "- Source asset assumptions listed.\n"
            "- Remix matrix rules drafted.\n"
            "- Batch review and publishing boundaries clarified.\n"
        ),
        tasks=(
            DemoTaskTemplate(
                title="Identify source materials and constraints",
                executor_slot="ceo_agent_slot",
                expected_output="Inputs, constraints, and review boundary.",
                audit_summary="CEO Agent framed source asset constraints.",
            ),
            DemoTaskTemplate(
                title="Draft remix matrix rules",
                executor_slot="codex_slot",
                expected_output="Matrix dimensions and batch naming rules.",
                audit_summary="Codex slot drafted deterministic matrix rules.",
            ),
            DemoTaskTemplate(
                title="Review platform and brand risks",
                executor_slot="claude_slot",
                expected_output="Risk notes and manual review triggers.",
                audit_summary="Claude slot reviewed brand and platform risks.",
            ),
            DemoTaskTemplate(
                title="Assemble batch execution brief",
                executor_slot="local_script_slot",
                expected_output="Batch plan and Founder review checklist.",
                audit_summary="Local script slot assembled the workflow brief.",
            ),
        ),
    ),
)

OFFERS_BY_ID = {offer.offer_id: offer for offer in OFFERS}


__all__ = [
    "DEMO_MODE",
    "DEMO_SOURCE_PATH",
    "OFFERS",
    "OFFERS_BY_ID",
    "PILOT_AUTHORITY",
    "DemoOffer",
    "DemoTaskTemplate",
]
