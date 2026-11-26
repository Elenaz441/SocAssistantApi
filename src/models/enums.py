from typing import Literal

IncidentCategory = Literal[
    "brute_force", "phishing", "malware", "data_exfiltration",
    "misconfiguration", "vulnerability", "lost_device", "other",
]
Severity = Literal["low", "medium", "high", "critical"]
Impact = Literal["confidentiality", "integrity", "availability", "none"]
Team = Literal["soc_l1", "soc_l2", "ir_team", "appsec", "it_ops"]
WorkflowName = Literal["one_shot", "sequential"]

TEAM_BY_CATEGORY = {
    "brute_force": "soc_l1",
    "phishing": "soc_l1",
    "malware": "ir_team",
    "data_exfiltration": "ir_team",
    "misconfiguration": "it_ops",
    "vulnerability": "appsec",
    "lost_device": "it_ops",
    "other": "soc_l1",
}
