"""Canonical attempt identity for governed execution retries."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json, re
_ID_RE = re.compile(r"^[^\s]{1,256}$")
class AttemptIdentityError(ValueError): pass
def _id(value: str, name: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise AttemptIdentityError(f"{name} must be a non-empty bounded identifier")
    return value
@dataclass(frozen=True)
class CanonicalAttempt:
    mission_id: str
    work_id: str
    task_id: str
    run_id: str
    attempt_id: str
    attempt_number: int
    retry_of: str | None = None
    def __post_init__(self) -> None:
        for name, value in (("mission_id",self.mission_id),("work_id",self.work_id),("task_id",self.task_id),("run_id",self.run_id),("attempt_id",self.attempt_id)):
            _id(value,name)
        if type(self.attempt_number) is not int or self.attempt_number < 1:
            raise AttemptIdentityError("attempt_number must be a positive integer")
        if self.retry_of is not None:
            _id(self.retry_of,"retry_of")
            if self.retry_of == self.attempt_id:
                raise AttemptIdentityError("attempt cannot retry itself")
            if self.attempt_number == 1:
                raise AttemptIdentityError("first attempt cannot have retry_of")
    @property
    def is_retry(self) -> bool:
        return self.retry_of is not None
    def retry(self, *, attempt_id: str) -> "CanonicalAttempt":
        return CanonicalAttempt(self.mission_id,self.work_id,self.task_id,self.run_id,attempt_id,self.attempt_number+1,self.attempt_id)
    def as_mapping(self) -> dict[str, str | int | None]:
        return {"mission_id":self.mission_id,"work_id":self.work_id,"task_id":self.task_id,"run_id":self.run_id,"attempt_id":self.attempt_id,"attempt_number":self.attempt_number,"retry_of":self.retry_of}
    def fingerprint(self) -> str:
        material=json.dumps(self.as_mapping(),sort_keys=True,separators=(",",":")).encode()
        return hashlib.sha256(material).hexdigest()
def first_attempt(*, mission_id: str, work_id: str, task_id: str, run_id: str, attempt_id: str) -> CanonicalAttempt:
    return CanonicalAttempt(mission_id,work_id,task_id,run_id,attempt_id,1)
def assert_same_attempt_lineage(previous: CanonicalAttempt, current: CanonicalAttempt) -> None:
    for field in ("mission_id","work_id","task_id","run_id"):
        if getattr(previous,field) != getattr(current,field):
            raise AttemptIdentityError(f"{field} attempt lineage conflict")
    if current.retry_of != previous.attempt_id:
        raise AttemptIdentityError("retry_of must point to the immediately previous attempt")
    if current.attempt_number != previous.attempt_number + 1:
        raise AttemptIdentityError("attempt_number must increment exactly by one")
    if current.attempt_id == previous.attempt_id:
        raise AttemptIdentityError("retry must use a unique attempt_id")
