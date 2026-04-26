# AWS

Studies in AWS architecture.

## Projects

| Project | Path | Description | Status |
| --- | --- | --- | --- |
| DIY Q Business Chatbot | `diy-q-business-chatbot/` | Self-managed RAG chatbot as an alternative to Q Business | Active |
| DIY Dovecot | `diy-dovecot/` | Self-managed Dovecot mail server | Planned |
| Drawing Containers | `drawing-containers/` | Containerized ML pipeline for drawing generation | Active |
| IMAP Resilience | `imap-resilience/` | Automated recovery for a single-instance IMAP mail server | Active |
| Protect the Raspberry Pi | `protect-the-raspberry-pi/` | Filtering illegitimate traffic to a Raspberry Pi web server via CloudFront | Active |
| RDS Cross-Account IAM Auth | `rds-cross-account-iam-authentication/` | Cross-account IAM authentication for RDS MySQL | Active |
| VPC Planning | `vpc-planning/` | Naming conventions and CIDR block planning for VPCs | Active |

## Conventions

- Each project is independent. Changes stay within the target project directory.
- Commit messages are prefixed with the project name: `[project-name] description`.
- Root-level commits use `[root]`: `[root] Update project index`.
- Project-specific ignore rules, dependencies, and configuration live inside the project directory.
