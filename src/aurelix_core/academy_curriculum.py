"""Canonical Academy curriculum and durable capability-growth state.

This is not a second Academy. It is the curriculum/governance layer attached to
AURELIX's existing AcademyEngine. It gives the Academy a complete role/skill
catalog, durable progress, and a controlled way to discover useful skills that
were not known when the catalog was authored.

The Academy can learn and propose; it never grants execution authority.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable


@dataclass(frozen=True)
class CurriculumSkill:
    skill_id: str
    name: str
    category: str
    prerequisites: tuple[str, ...] = ()


@dataclass(frozen=True)
class CurriculumRole:
    role_id: str
    name: str
    skills: tuple[str, ...]


@dataclass(frozen=True)
class SkillGap:
    gap_id: str
    skill_id: str
    reason: str
    source: str
    discovered_at: str
    confidence: float
    status: str = "open"


class AcademyCurriculum:
    """One canonical learning catalog shared by Academy, memory and intelligence."""

    CATEGORIES = {
        "role",
        "skill",
        "beginner",
        "best_practice",
    }

    ROLE_SKILLS: dict[str, tuple[str, ...]] = {
        "power-bi": ("power-bi", "sql", "python-data-analysis", "data-analysis", "bi-analysis"),
        "product-design": ("product-design", "ux-design", "design-systems", "system-design", "product-creation"),
        "ai-engineer": ("python", "ai-agents", "machine-learning", "prompt-engineering", "system-design", "docker", "kubernetes"),
        "frontend": ("html", "css", "javascript", "react", "vue", "angular", "nextjs"),
        "backend": ("python", "nodejs", "sql", "postgresql", "redis", "api-design", "backend-performance"),
        "full-stack": ("frontend", "backend", "system-design", "git-github"),
        "android": ("kotlin", "react-native", "mobile-design"),
        "devops": ("linux", "docker", "kubernetes", "aws", "terraform", "shell-bash"),
        "devsecops": ("devops", "api-security", "cybersecurity", "security-testing"),
        "data-analyst": ("python-data-analysis", "sql", "power-bi", "data-analysis"),
        "ai-data-scientist": ("python-data-analysis", "machine-learning", "data-analysis", "statistics"),
        "data-engineer": ("python", "sql", "postgresql", "mongodb", "redis", "elasticsearch", "data-engineering"),
        "machine-learning": ("python", "machine-learning", "data-analysis", "mlops", "agents-ai"),
        "postgresql": ("postgresql", "sql", "database-design", "performance-engineering"),
        "ios": ("swift", "swiftui", "react-native", "mobile-design"),
        "blockchain": ("blockchain", "rust", "go", "security-testing"),
        "qa": ("quality-assurance", "python", "sql", "docker", "test-design"),
        "software-architect": ("system-design", "architecture-design", "api-design", "security-testing"),
        "api-design": ("api-design", "api-security", "backend-performance", "system-design"),
        "cybersecurity": ("cybersecurity", "api-security", "linux", "shell-bash", "devsecops"),
        "ux-design": ("ux-design", "design-systems", "product-design"),
        "technical-writer": ("technical-writing", "system-design", "api-design"),
        "game-developer": ("game-development", "c-plus-plus", "c", "unity-or-equivalent"),
        "server-game-developer": ("game-development", "backend", "nodejs", "go", "rust"),
        "mlops": ("machine-learning", "mlops", "docker", "kubernetes", "aws", "terraform"),
        "product-manager": ("product-management", "product-design", "data-analysis", "system-design"),
        "engineering-manager": ("engineering-management", "system-design", "code-review", "devops"),
        "developer-relations": ("developer-relations", "technical-writing", "javascript", "python"),
        "bi-analyst": ("bi-analysis", "power-bi", "sql", "data-analysis"),
        "ai-red-team": ("ai-red-teaming", "cybersecurity", "api-security", "prompt-engineering"),
        "network-engineer": ("network-engineering", "linux", "kubernetes", "cybersecurity"),
        "forward-deployed-engineer": ("python", "api-design", "devops", "product-design", "developer-relations"),
    }

    SKILLS: tuple[CurriculumSkill, ...] = tuple(
        CurriculumSkill(skill_id=name, name=name, category="skill")
        for name in sorted({skill for skills in ROLE_SKILLS.values() for skill in skills})
    ) + (
        CurriculumSkill("code-claude", "Code Claude", "skill"),
        CurriculumSkill("python-data-analysis", "Python for Data Analysis", "skill"),
        CurriculumSkill("vibe-coding", "Vibe Coding", "skill"),
        CurriculumSkill("leetcode", "LeetCode", "skill"),
        CurriculumSkill("computer-science", "Computer Science", "skill"),
        CurriculumSkill("openclaw", "OpenClaw", "skill"),
        CurriculumSkill("typescript", "TypeScript", "skill"),
        CurriculumSkill("java", "Java", "skill"),
        CurriculumSkill("aspnet-core", "ASP.NET Core", "skill"),
        CurriculumSkill("spring-boot", "Spring Boot", "skill"),
        CurriculumSkill("flutter", "Flutter", "skill"),
        CurriculumSkill("c", "C", "skill"),
        CurriculumSkill("c-plus-plus", "C++", "skill"),
        CurriculumSkill("rust", "Rust", "skill"),
        CurriculumSkill("go", "Go", "skill"),
        CurriculumSkill("ai-product-builders", "AI Product Builders", "skill"),
        CurriculumSkill("react-native", "React Native", "skill"),
        CurriculumSkill("mongodb", "MongoDB", "skill"),
        CurriculumSkill("php", "PHP", "skill"),
        CurriculumSkill("cloudflare", "Cloudflare", "skill"),
        CurriculumSkill("agents-ai", "AI Agents", "skill"),
        CurriculumSkill("kotlin", "Kotlin", "skill"),
        CurriculumSkill("html", "HTML", "skill"),
        CurriculumSkill("css", "CSS", "skill"),
        CurriculumSkill("swift", "Swift", "skill"),
        CurriculumSkill("swiftui", "SwiftUI", "skill"),
        CurriculumSkill("laravel", "Laravel", "skill"),
        CurriculumSkill("elasticsearch", "Elasticsearch", "skill"),
        CurriculumSkill("wordpress", "WordPress", "skill"),
        CurriculumSkill("django", "Django", "skill"),
        CurriculumSkill("ruby", "Ruby", "skill"),
        CurriculumSkill("ruby-on-rails", "Ruby on Rails", "skill"),
        CurriculumSkill("scala", "Scala", "skill"),
        CurriculumSkill("beginner-frontend", "Beginner Frontend Development", "beginner"),
        CurriculumSkill("beginner-backend", "Beginner Backend Development", "beginner"),
        CurriculumSkill("beginner-devops", "Beginner DevOps", "beginner"),
        CurriculumSkill("git-github-beginner", "Git and GitHub for Beginners", "beginner"),
        CurriculumSkill("aws", "AWS", "best_practice"),
        CurriculumSkill("api-security", "API Security", "best_practice"),
        CurriculumSkill("backend-performance", "Backend Performance", "best_practice"),
        CurriculumSkill("frontend-performance", "Frontend Performance", "best_practice"),
        CurriculumSkill("code-review", "Code Review", "best_practice"),
        CurriculumSkill("sql", "SQL", "skill"),
        CurriculumSkill("python", "Python", "skill"),
        CurriculumSkill("postgresql", "PostgreSQL", "skill"),
        CurriculumSkill("javascript", "JavaScript", "skill"),
        CurriculumSkill("nodejs", "Node.js", "skill"),
        CurriculumSkill("react", "React", "skill"),
        CurriculumSkill("vue", "Vue", "skill"),
        CurriculumSkill("angular", "Angular", "skill"),
        CurriculumSkill("nextjs", "Next.js", "skill"),
        CurriculumSkill("system-design", "System Design", "skill"),
        CurriculumSkill("architecture-design", "Architecture Design", "skill"),
        CurriculumSkill("design-systems", "Design Systems", "skill"),
        CurriculumSkill("prompt-engineering", "Prompt Engineering", "skill"),
        CurriculumSkill("mongodb", "MongoDB", "skill"),
        CurriculumSkill("linux", "Linux", "skill"),
        CurriculumSkill("kubernetes", "Kubernetes", "skill"),
        CurriculumSkill("docker", "Docker", "skill"),
        CurriculumSkill("terraform", "Terraform", "skill"),
        CurriculumSkill("redis", "Redis", "skill"),
        CurriculumSkill("git-github", "Git and GitHub", "skill"),
        CurriculumSkill("cloudflare", "Cloudflare", "skill"),
        CurriculumSkill("shell-bash", "Shell / Bash", "skill"),
        CurriculumSkill("innovation", "AI Product Builders", "skill"),
        CurriculumSkill("ai-red-teaming", "AI Red Teaming", "skill"),
        CurriculumSkill("cybersecurity", "Cybersecurity", "skill"),
        CurriculumSkill("quality-assurance", "Quality Assurance", "skill"),
        CurriculumSkill("test-design", "Test Design", "skill"),
        CurriculumSkill("technical-writing", "Technical Writing", "skill"),
        CurriculumSkill("product-design", "Product Design", "skill"),
        CurriculumSkill("ux-design", "UX Design", "skill"),
        CurriculumSkill("product-management", "Product Management", "skill"),
        CurriculumSkill("engineering-management", "Engineering Management", "skill"),
        CurriculumSkill("developer-relations", "Developer Relations", "skill"),
        CurriculumSkill("bi-analysis", "BI Analysis", "skill"),
        CurriculumSkill("data-analysis", "Data Analysis", "skill"),
        CurriculumSkill("statistics", "Statistics", "skill"),
        CurriculumSkill("data-engineering", "Data Engineering", "skill"),
        CurriculumSkill("machine-learning", "Machine Learning", "skill"),
        CurriculumSkill("mlops", "MLOps", "skill"),
        CurriculumSkill("network-engineering", "Network Engineering", "skill"),
        CurriculumSkill("blockchain", "Blockchain", "skill"),
        CurriculumSkill("game-development", "Game Development", "skill"),
        CurriculumSkill("mobile-design", "Mobile Design", "skill"),
        CurriculumSkill("api-design", "API Design", "skill"),
        CurriculumSkill("database-design", "Database Design", "skill"),
        CurriculumSkill("performance-engineering", "Performance Engineering", "skill"),
        CurriculumSkill("security-testing", "Security Testing", "skill"),
        CurriculumSkill("unity-or-equivalent", "Game Engine Development", "skill"),
    )

    BEGINNER_SKILLS = (
        "beginner-frontend",
        "beginner-backend",
        "beginner-devops",
        "git-github-beginner",
    )

    def __init__(self, store=None) -> None:
        self.store = store
        self._skills = {item.skill_id: item for item in self.SKILLS}
        self._roles = {
            role_id: CurriculumRole(role_id, role_id.replace("-", " ").title(), skills)
            for role_id, skills in self.ROLE_SKILLS.items()
        }
        self._progress: dict[str, dict[str, object]] = {}
        self._gaps: dict[str, SkillGap] = {}
        self._load()

    def _load(self) -> None:
        if self.store is None:
            return
        with self.store.lock:
            rows = self.store.db.execute(
                "SELECT key,value FROM runtime_state WHERE key LIKE 'academy-curriculum:%'"
            ).fetchall()
        for row in rows:
            try:
                payload = json.loads(row["value"])
            except (TypeError, json.JSONDecodeError):
                continue
            key = str(row["key"])
            if key == "academy-curriculum:progress":
                self._progress = payload
            elif key == "academy-curriculum:gaps":
                self._gaps = {
                    item["gap_id"]: SkillGap(**item) for item in payload
                }

    def _persist(self) -> None:
        if self.store is None:
            return
        with self.store.lock, self.store.db:
            self.store.db.execute(
                "INSERT INTO runtime_state(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                ("academy-curriculum:progress", json.dumps(self._progress, sort_keys=True)),
            )
            self.store.db.execute(
                "INSERT INTO runtime_state(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                ("academy-curriculum:gaps", json.dumps([asdict(item) for item in self._gaps.values()], sort_keys=True)),
            )

    def roles(self) -> tuple[CurriculumRole, ...]:
        return tuple(self._roles.values())

    def skills(self) -> tuple[CurriculumSkill, ...]:
        return tuple(self._skills.values())

    def role_skills(self, role_id: str) -> tuple[CurriculumSkill, ...]:
        role = self._roles[role_id]
        return tuple(self._skills[name] for name in role.skills if name in self._skills)

    def status(self, skill_id: str) -> str:
        return str(self._progress.get(skill_id, {}).get("status", "not_started"))

    def mark_learned(self, skill_id: str, *, evidence_refs: Iterable[str] = (), confidence: float = 0.0) -> None:
        if skill_id not in self._skills:
            raise KeyError(skill_id)
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        self._progress[skill_id] = {
            "status": "learned",
            "confidence": confidence,
            "evidence_refs": sorted({str(ref) for ref in evidence_refs if str(ref).strip()}),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._persist()

    def discover_gap(self, *, name: str, reason: str, source: str, confidence: float = 0.5) -> SkillGap:
        """Register a new useful capability without granting execution authority."""
        normalized = "-".join(name.strip().casefold().split())
        if not normalized:
            raise ValueError("skill name is required")
        if not reason.strip() or not source.strip():
            raise ValueError("reason and source are required")
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if normalized in self._skills:
            existing = self._progress.get(normalized, {})
            if existing.get("status") == "learned":
                return SkillGap(normalized, normalized, "already learned", source, datetime.now(timezone.utc).isoformat(), 1.0, "resolved")
        gap_id = f"gap:{normalized}"
        gap = SkillGap(gap_id, normalized, reason.strip(), source.strip(), datetime.now(timezone.utc).isoformat(), confidence)
        self._gaps[gap_id] = gap
        self._persist()
        return gap

    def open_gaps(self) -> tuple[SkillGap, ...]:
        return tuple(item for item in self._gaps.values() if item.status == "open")

    def roadmap(self, role_id: str) -> dict[str, object]:
        skills = self.role_skills(role_id)
        return {
            "role": role_id,
            "skills": [
                {"skill_id": skill.skill_id, "name": skill.name, "status": self.status(skill.skill_id)}
                for skill in skills
            ],
            "remaining": [skill.skill_id for skill in skills if self.status(skill.skill_id) != "learned"],
        }

    def discover_from_requirement(self, requirement: str, *, source: str = "system") -> SkillGap | None:
        """Turn an unknown technical requirement into a durable Academy gap."""
        normalized = "-".join(requirement.strip().casefold().split())
        if not normalized or normalized in self._skills:
            return None
        return self.discover_gap(
            name=requirement,
            reason="required by an observed system task but absent from the canonical curriculum",
            source=source,
            confidence=0.5,
        )
