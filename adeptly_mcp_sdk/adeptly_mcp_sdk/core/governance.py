import re
REQUIRED = ["objective","citations","risks","next steps"]

def review_text(text: str) -> tuple[bool,list[str]]:
    issues=[]
    if not re.search(r"https?://", text): issues.append("Missing citation URL(s)")
    for sec in REQUIRED:
        if sec not in text.lower(): issues.append(f"Missing section: {sec}")
    return (len(issues)==0, issues)
