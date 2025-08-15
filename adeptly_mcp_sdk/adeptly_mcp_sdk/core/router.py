class Router:
    def route(self, task: str) -> list[str]:
        t = task.lower()
        if "lead" in t or "sequence" in t: return ["sales","governance"]
        if "blog" in t or "calendar" in t: return ["marketing","content_creator","governance"]
        return ["governance"]
