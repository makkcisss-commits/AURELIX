"""Enterprise context for profiles, assets, and evolving competencies.

This module intentionally does not replace Identity, Academy, Learning,
Opportunity, Governor, Runtime, Business, or Revenue. It provides the thin
business-context layer that lets those domains refer back to the enterprise
profile and the resources/capabilities involved in an outcome.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from uuid import uuid4


class ProfileKind(str, Enum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    TEAM = "TEAM"
    BUSINESS = "BUSINESS"


class AssetKind(str, Enum):
    DIGITAL = "DIGITAL"
    INTELLECTUAL = "INTELLECTUAL"
    DATA = "DATA"
    PRODUCT = "PRODUCT"
    SERVICE = "SERVICE"
    CHANNEL = "CHANNEL"
    ACCOUNT = "ACCOUNT"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    CAPABILITY = "CAPABILITY"
    RELATIONSHIP = "RELATIONSHIP"


class AssetStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"


@dataclass(frozen=True)
class Profile:
    profile_id: str
    identity_id: str
    name: str
    kind: ProfileKind = ProfileKind.PERSON
    description: str = ""


@dataclass(frozen=True)
class Asset:
    asset_id: str
    profile_id: str
    name: str
    kind: AssetKind
    scope: str
    description: str = ""
    status: AssetStatus = AssetStatus.ACTIVE
    estimated_value_eur: Decimal = Decimal("0")


@dataclass(frozen=True)
class Competency:
    competency_id: str
    profile_id: str
    domain: str
    name: str
    level: float = 0.0
    confidence: float = 0.0
    evidence_refs: tuple[str, ...] = ()
    knowledge_refs: tuple[str, ...] = ()
    learning_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class EnterpriseLink:
    profile_id: str
    asset_ids: tuple[str, ...] = ()
    competency_ids: tuple[str, ...] = ()
    knowledge_refs: tuple[str, ...] = ()
    learning_refs: tuple[str, ...] = ()
    opportunity_id: str | None = None
    experiment_id: str | None = None
    runtime_execution_id: str | None = None
    business_activity_id: str | None = None
    revenue_source_id: str | None = None


class EnterpriseRegistry:
    """Small V1 registry for enterprise context; no authorization logic."""

    def __init__(self) -> None:
        self.profiles: dict[str, Profile] = {}
        self.assets: dict[str, Asset] = {}
        self.competencies: dict[str, Competency] = {}
        self.links: list[EnterpriseLink] = []

    def create_profile(self, *, identity_id: str, name: str,
                       kind: ProfileKind = ProfileKind.PERSON,
                       description: str = "") -> Profile:
        if not identity_id.strip() or not name.strip():
            raise ValueError("identity_id and name are required")
        profile = Profile(str(uuid4()), identity_id, name, kind, description)
        self.profiles[profile.profile_id] = profile
        return profile

    def register_asset(self, *, profile_id: str, name: str,
                       kind: AssetKind, scope: str, description: str = "",
                       estimated_value_eur: Decimal = Decimal("0")) -> Asset:
        self._require_profile(profile_id)
        if not name.strip() or not scope.strip():
            raise ValueError("name and scope are required")
        if estimated_value_eur < 0:
            raise ValueError("estimated asset value cannot be negative")
        asset = Asset(str(uuid4()), profile_id, name, kind, scope,
                      description, AssetStatus.ACTIVE, estimated_value_eur)
        self.assets[asset.asset_id] = asset
        return asset

    def register_competency(self, *, profile_id: str, domain: str, name: str,
                            level: float = 0.0, confidence: float = 0.0,
                            evidence_refs: tuple[str, ...] = (),
                            knowledge_refs: tuple[str, ...] = (),
                            learning_refs: tuple[str, ...] = ()) -> Competency:
        self._require_profile(profile_id)
        if not domain.strip() or not name.strip():
            raise ValueError("domain and name are required")
        if not 0 <= level <= 1 or not 0 <= confidence <= 1:
            raise ValueError("level and confidence must be between 0 and 1")
        competency = Competency(
            str(uuid4()), profile_id, domain, name, level, confidence,
            tuple(evidence_refs), tuple(knowledge_refs), tuple(learning_refs),
        )
        self.competencies[competency.competency_id] = competency
        return competency

    def link(self, *, profile_id: str, asset_ids: tuple[str, ...] = (),
             competency_ids: tuple[str, ...] = (), knowledge_refs: tuple[str, ...] = (),
             learning_refs: tuple[str, ...] = (), opportunity_id: str | None = None,
             experiment_id: str | None = None, runtime_execution_id: str | None = None,
             business_activity_id: str | None = None,
             revenue_source_id: str | None = None) -> EnterpriseLink:
        self._require_profile(profile_id)
        for asset_id in asset_ids:
            asset = self.assets.get(asset_id)
            if asset is None or asset.profile_id != profile_id:
                raise ValueError("asset does not belong to profile")
        for competency_id in competency_ids:
            competency = self.competencies.get(competency_id)
            if competency is None or competency.profile_id != profile_id:
                raise ValueError("competency does not belong to profile")
        if not any((knowledge_refs, learning_refs, opportunity_id, experiment_id,
                    runtime_execution_id, business_activity_id, revenue_source_id)):
            raise ValueError("link requires a downstream or intelligence reference")
        link = EnterpriseLink(
            profile_id, tuple(asset_ids), tuple(competency_ids), tuple(knowledge_refs),
            tuple(learning_refs), opportunity_id, experiment_id,
            runtime_execution_id, business_activity_id, revenue_source_id,
        )
        self.links.append(link)
        return link

    def _require_profile(self, profile_id: str) -> None:
        if profile_id not in self.profiles:
            raise KeyError(profile_id)
