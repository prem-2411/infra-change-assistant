"""Rule-based risk check. Pure Python, no I/O: used when the LLM is unavailable or fails."""
import re
from dataclasses import dataclass, field

HIGH_SIGNALS = [
    (r"0\.0\.0\.0/0|::/0|\bany ip\b|\bfrom any\b|\ball traffic\b", "opens access to the whole internet"),
    (r"disable\w*\s+(mfa|2fa|multi-factor)|turn\w* off (mfa|2fa)", "weakens authentication (MFA)"),
    (r"disable\w*\s+(audit|logging)|turn\w* off (audit|logging)", "reduces audit logging"),
    (r"domain admin|\broot\b|sudo nopasswd|\bpermanent\b", "grants broad or permanent privilege"),
    (r"plain http|plaintext|unencrypted|\bftp\b|\btelnet\b", "uses unencrypted transport or storage"),
    (r"api key|password|secret|token", "may expose a secret"),
    (r"\bdelete\b|\bdrop\b|\bwipe\b|decommission", "destructive change"),
]
MEDIUM_SIGNALS = [
    (r"\bprod(uction)?\b", "touches production"),
    (r"\b(admin|privileged|write access)\b", "elevated access"),
    (r"\b(22|23|3389|445|1433|3306|5432|6379)\b|\bssh\b|\brdp\b", "sensitive network port"),
    (r"\b(firewall|vpn|iam|dns|certificate|database|bastion)\b", "security-relevant component"),
]
MITIGATIONS = r"rollback|roll back|revert|change window|window (sunday|saturday|monday|tuesday|wednesday|thursday|friday)"
LEVEL = {"low": 0, "medium": 1, "high": 2}


@dataclass
class RuleResult:
    risk: str
    reasons: list[str] = field(default_factory=list)


def assess(type_: str, target: str, justification: str, risk_level: str) -> RuleResult:
    text = f"{target} {justification}".lower()
    score = 0
    reasons: list[str] = []
    for pattern, reason in HIGH_SIGNALS:
        if re.search(pattern, text):
            score += 3
            reasons.append(f"Signal: {reason}")
    medium_hits = [reason for pattern, reason in MEDIUM_SIGNALS if re.search(pattern, text)]
    score += min(len(medium_hits), 2)
    reasons.extend(f"Signal: {r}" for r in medium_hits)
    if len(justification) < 40:
        score += 1
        reasons.append("Justification is very short")
    if re.search(MITIGATIONS, text):
        score -= 1
        reasons.append("Mentions rollback or a change window (lowers risk slightly)")
    score += LEVEL.get(risk_level, 1)
    risk = "high" if score >= 4 else "medium" if score >= 2 else "low"
    if not reasons:
        reasons.append("No risk signals found by the keyword rules")
    return RuleResult(risk=risk, reasons=reasons)
