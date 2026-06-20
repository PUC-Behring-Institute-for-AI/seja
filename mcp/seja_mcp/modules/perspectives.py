def register_tools(mcp):

    _perspectives = [
        {
            "id": "p1",
            "name": "Semiotic Perfection",
            "depth": 3,
            "depth_factor": 3,
            "questions": [
                "How does this design express the developer's intent?",
                "What semiotic signs are present/absent?",
                "Is there metacommunicative noise in the interface?",
            ],
        },
        {
            "id": "p2",
            "name": "Cognitive Load",
            "depth": 2,
            "depth_factor": 2,
            "questions": [
                "How much cognitive effort does this require?",
                "Are patterns consistent with user mental models?",
            ],
        },
        {
            "id": "p3",
            "name": "Error Resilience",
            "depth": 3,
            "depth_factor": 3,
            "questions": [
                "What failure modes exist?",
                "How does the system degrade?",
                "Are error messages semiotically transparent?",
            ],
        },
        {
            "id": "p4",
            "name": "Temporal Coupling",
            "depth": 2,
            "depth_factor": 2,
            "questions": [
                "Are there implicit ordering dependencies?",
                "Can operations be reordered safely?",
            ],
        },
        {
            "id": "p5",
            "name": "Boundary Integrity",
            "depth": 3,
            "depth_factor": 3,
            "questions": [
                "Where are the system boundaries?",
                "What crosses them and how?",
                "Are boundaries enforced or conventional?",
            ],
        },
        {
            "id": "p6",
            "name": "Intent Visibility",
            "depth": 2,
            "depth_factor": 2,
            "questions": [
                "Can a reader infer the original intent?",
                "Is the 'why' documented near the 'what'?",
            ],
        },
        {
            "id": "p7",
            "name": "Abstraction Fit",
            "depth": 3,
            "depth_factor": 3,
            "questions": [
                "Do abstractions match the domain?",
                "Are there leaky abstractions?",
                "What is the abstraction overhead vs benefit?",
            ],
        },
        {
            "id": "p8",
            "name": "State Explosion",
            "depth": 2,
            "depth_factor": 2,
            "questions": [
                "How many states exist implicitly?",
                "Are all states reachable and recoverable?",
            ],
        },
        {
            "id": "p9",
            "name": "Naming Semiotics",
            "depth": 2,
            "depth_factor": 2,
            "questions": [
                "Do names reveal intent or obscure it?",
                "Are there naming inconsistencies?",
            ],
        },
        {
            "id": "p10",
            "name": "Evolution Pathway",
            "depth": 3,
            "depth_factor": 3,
            "questions": [
                "How does this design accommodate change?",
                "What makes future modifications easy/hard?",
                "Is there a clear migration path?",
            ],
        },
        {
            "id": "p11",
            "name": "Metacommunicative Gap",
            "depth": 3,
            "depth_factor": 3,
            "questions": [
                "What does the user expect vs what exists?",
                "Where is the gap between intention and interpretation?",
                "How can the gap be measured?",
            ],
        },
        {
            "id": "p12",
            "name": "Feedback Quality",
            "depth": 2,
            "depth_factor": 2,
            "questions": [
                "Is feedback timely and informative?",
                "Does feedback help the user form correct mental models?",
            ],
        },
        {
            "id": "p13",
            "name": "Consistency Audit",
            "depth": 2,
            "depth_factor": 2,
            "questions": [
                "Are similar things expressed similarly?",
                "Are there violations of the principle of least astonishment?",
            ],
        },
        {
            "id": "p14",
            "name": "Dependency Direction",
            "depth": 3,
            "depth_factor": 3,
            "questions": [
                "Do dependencies flow in the right direction?",
                "Are there circular dependencies?",
                "Is the dependency graph a DAG?",
            ],
        },
        {
            "id": "p15",
            "name": "Protocol Completeness",
            "depth": 2,
            "depth_factor": 2,
            "questions": [
                "Are all conversational turns accounted for?",
                "Is there an explicit interaction protocol?",
            ],
        },
        {
            "id": "p16",
            "name": "Emergent Complexity",
            "depth": 3,
            "depth_factor": 3,
            "questions": [
                "What complexity emerges from the interactions?",
                "Is the whole greater (or lesser) than the sum of parts?",
                "Are there second-order effects?",
            ],
        },
    ]

    @mcp.tool
    async def get_for_plan(workspace_path: str, plan_id: str) -> dict:
        return {
            "status": "ok",
            "perspectives": _perspectives,
            "count": len(_perspectives),
        }

    @mcp.tool
    async def get_perspective(workspace_path: str, perspective_id: str) -> dict:
        for p in _perspectives:
            if p["id"] == perspective_id:
                return {"status": "ok", "perspective": p}
        return {"status": "not_found"}
