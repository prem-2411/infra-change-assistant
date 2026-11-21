SEED_POLICIES = [
    {"title": "No public access to admin ports", "category": "network",
     "rule_text": "Inbound rules must never allow 0.0.0.0/0 or any-IP access to administrative or database ports "
                  "(22, 3389, 3306, 5432, 1433, 6379). Use the VPN or a bastion host."},
    {"title": "Production change windows", "category": "change-management",
     "rule_text": "Changes to production systems need a scheduled change window and a written rollback plan in "
                  "the justification."},
    {"title": "Least privilege access", "category": "access",
     "rule_text": "Access grants must be time-bound and scoped to the minimum role. Admin, root or domain-admin "
                  "access needs manager approval and an expiry date. Permanent privileged access is prohibited."},
    {"title": "MFA is mandatory", "category": "authentication",
     "rule_text": "Multi-factor authentication must stay enabled on every account. Disabling or bypassing MFA "
                  "is prohibited."},
    {"title": "Audit logging stays on", "category": "logging",
     "rule_text": "Audit logging must not be disabled or reduced on any system, including for performance reasons."},
    {"title": "Encryption in transit and at rest", "category": "data-protection",
     "rule_text": "Data stores must be encrypted at rest. Plaintext protocols (HTTP, FTP, Telnet) are prohibited "
                  "for customer or sensitive data."},
    {"title": "New server standards", "category": "servers",
     "rule_text": "New servers must use the approved hardened base image, carry owner and cost-center tags, and be "
                  "registered in the inventory."},
    {"title": "Configuration change review", "category": "change-management",
     "rule_text": "Configuration changes to shared services need peer review and must be tested in staging first."},
    {"title": "Destructive changes need backups", "category": "data-protection",
     "rule_text": "Deleting data or decommissioning systems requires a verified, restore-tested backup and "
                  "data-owner sign-off."},
    {"title": "Secrets management", "category": "secrets",
     "rule_text": "Secrets (API keys, passwords, tokens) must live in the approved secrets manager, never in "
                  "config files, code or repositories."},
]
