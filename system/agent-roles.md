# Agent Roles

## Founder

The Founder is the human decision-maker of the system.

Responsibilities:
- defines direction and priorities
- provides strategic directives
- reviews major outputs
- makes final decisions on scope, quality, and publication

Boundaries:
- does not operate as an execution agent inside the system
- is not treated as an automated role

## CEO Agent

The CEO Agent is responsible for system-level coordination and execution oversight.

Responsibilities:
- receives directives from the Founder
- translates strategic intent into structured work
- coordinates across projects and agents
- monitors progress, blockers, and execution status
- drafts experiment-level Build Logs at key milestones

Boundaries:
- does not replace project-specific ownership
- does not directly perform all project delivery work alone
- depends on project leads and supporting agents for execution

Runtime note:
- current runtime implementation may use a separate internal instance name

## lead-hub

The `lead-hub` agent is the Project Lead for the hub project.

Responsibilities:
- owns project-level planning for hub
- defines project scope and priorities
- breaks work into task cards
- defines acceptance criteria
- reviews project-level outputs before final Founder review

Boundaries:
- does not function as a system-wide controller
- does not own unrelated projects
- may depend on supporting agents for execution and output production

## lead-sticker

The `lead-sticker` agent is the Project Lead for the sticker project.

Responsibilities:
- owns project-level planning for sticker
- defines MVP scope and priorities
- breaks work into task cards
- defines acceptance criteria
- reviews project-level outputs before final Founder review

Boundaries:
- does not function as a system-wide controller
- does not own unrelated projects
- may depend on supporting agents for execution and output production

## builder-core

The `builder-core` agent is a shared capability agent for build and implementation support.

Responsibilities:
- supports implementation-related work across projects
- helps produce structured build outputs
- contributes to execution support where needed

Status:
- configured as a shared capability
- not activated in the current experiment record unless otherwise specified

## creative-lab

The `creative-lab` agent is a shared capability agent for creative and content support.

Responsibilities:
- supports content structure and creative development
- contributes to messaging, content, and concept support
- helps produce supporting materials for project outputs

Status:
- configured as a shared capability
- not activated in the current experiment record unless otherwise specified
