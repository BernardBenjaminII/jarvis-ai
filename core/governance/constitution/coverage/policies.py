from .contracts import *
from .models import CoveragePolicy

def default_coverage_policy()->CoveragePolicy:
    return CoveragePolicy(DEFAULT_LOW_USAGE_THRESHOLD,DEFAULT_PARTIAL_DOMAIN_COVERAGE_THRESHOLD,DEFAULT_GOVERNED_DOMAIN_COVERAGE_THRESHOLD,tuple(sorted(DEFAULT_GOVERNED_DOMAINS)))
