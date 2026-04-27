from __future__ import annotations

from pydantic import BaseModel


class TunProvisionPlan(BaseModel):
    interface_name: str
    mtu: int
    cidr: str
    route_targets: list[str]
    implemented: bool = False
    notes: list[str]


def build_tun_provision_plan(interface_name: str, mtu: int, cidr: str) -> TunProvisionPlan:
    return TunProvisionPlan(
        interface_name=interface_name,
        mtu=mtu,
        cidr=cidr,
        route_targets=[cidr],
        notes=[
            "Phase 3 will create the TUN device from /dev/net/tun inside the Linux VM.",
            "pyroute2 will own address assignment, route install/remove, and teardown.",
            "The current scaffold intentionally stops before mutating host networking.",
        ],
    )
