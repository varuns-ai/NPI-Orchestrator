"""One factory per NPI phase agent (Need, Concept, Bid, Develop, Validate, Launch)."""

from .bid import create_bid_agent
from .concept import create_concept_agent
from .develop import create_develop_agent
from .launch import create_launch_agent
from .need import create_need_agent
from .validate import create_validate_agent

__all__ = [
    "create_need_agent",
    "create_concept_agent",
    "create_bid_agent",
    "create_develop_agent",
    "create_validate_agent",
    "create_launch_agent",
    "AGENT_FACTORIES",
]

AGENT_FACTORIES = {
    "PH1": create_need_agent,
    "PH2": create_concept_agent,
    "PH3": create_bid_agent,
    "PH4": create_develop_agent,
    "PH5": create_validate_agent,
    "PH6": create_launch_agent,
}
