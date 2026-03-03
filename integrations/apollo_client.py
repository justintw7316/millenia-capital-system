"""
integrations/apollo_client.py — Apollo.io contact enrichment (STUBBED).

# TODO: WIRE REAL API — https://apolloio.github.io/apollo-api-docs/
# Used in Step 7a for investor contact enrichment.
"""
import random
from typing import List, Dict

from core.logger import get_logger

logger = get_logger(__name__)

# ─── Mock investor contact pool ───────────────────────────────────────────────
_MOCK_CONTACTS = [
    {
        "name": "Michael Chen",
        "email": "m.chen@sequoiacap.com",
        "phone": "+1-415-555-0101",
        "linkedin": "https://linkedin.com/in/michael-chen-vc",
        "twitter": "@mchen_vc",
        "website": "https://sequoiacap.com",
    },
    {
        "name": "Sarah Rodriguez",
        "email": "srodriguez@a16z.com",
        "phone": "+1-650-555-0202",
        "linkedin": "https://linkedin.com/in/sarah-rodriguez-a16z",
        "twitter": "@srodriguez_vc",
        "website": "https://a16z.com",
    },
    {
        "name": "James Thornton",
        "email": "j.thornton@khoslaventures.com",
        "phone": "+1-650-555-0303",
        "linkedin": "https://linkedin.com/in/james-thornton-kv",
        "twitter": "@jthornton_kv",
        "website": "https://khoslaventures.com",
    },
    {
        "name": "Priya Nair",
        "email": "priya@firstround.com",
        "phone": "+1-415-555-0404",
        "linkedin": "https://linkedin.com/in/priya-nair-vc",
        "twitter": "@priya_firstround",
        "website": "https://firstround.com",
    },
    {
        "name": "David Park",
        "email": "dpark@generalatlantic.com",
        "phone": "+1-212-555-0505",
        "linkedin": "https://linkedin.com/in/david-park-ga",
        "twitter": "@dpark_ga",
        "website": "https://generalatlantic.com",
    },
]


class ApolloClient:
    """STUBBED Apollo.io client. Returns realistic mock contact data."""

    def search_investors(self, criteria: Dict) -> List[Dict]:
        """
        Search for investors matching given criteria.

        # STUB CALL: search_investors
        # TODO: WIRE REAL API — POST https://api.apollo.io/v1/mixed_people/search
        Args:
            criteria: {industry, title_keywords, location, min_portfolio_size}
        Returns:
            List of investor contact dicts.
        """
        logger.debug(f"# STUB CALL: ApolloClient.search_investors(criteria={criteria})")
        results = [
            {
                **contact,
                "firm": contact["website"].replace("https://", "").replace("www.", "").split("/")[0],
                "title": random.choice(["General Partner", "Managing Partner", "Partner", "Principal"]),
                "industry_focus": criteria.get("industry", "technology"),
                "location": criteria.get("location", "San Francisco, CA"),
            }
            for contact in _MOCK_CONTACTS
        ]
        logger.info(f"[Apollo STUB] search_investors returned {len(results)} contacts")
        return results

    def enrich_contact(self, name: str, company: str) -> Dict:
        """
        Enrich a contact record with full details.

        # STUB CALL: enrich_contact
        # TODO: WIRE REAL API — POST https://api.apollo.io/v1/people/match
        Args:
            name: Contact full name.
            company: Company/firm name.
        Returns:
            Dict with {name, email, phone, linkedin, twitter, website}.
        """
        logger.debug(f"# STUB CALL: ApolloClient.enrich_contact(name={name!r}, company={company!r})")
        # Return first mock match or synthesize one
        for contact in _MOCK_CONTACTS:
            if name.split()[0].lower() in contact["name"].lower():
                logger.info(f"[Apollo STUB] Enriched {name!r} → {contact['email']}")
                return contact

        # Synthesize a contact if no mock match
        first, *rest = name.lower().split()
        last = rest[0] if rest else "contact"
        domain = company.lower().replace(" ", "") + ".com"
        synthesized = {
            "name": name,
            "email": f"{first}.{last}@{domain}",
            "phone": "+1-415-555-0000",
            "linkedin": f"https://linkedin.com/in/{first}-{last}",
            "twitter": f"@{first}_{last}",
            "website": f"https://{domain}",
        }
        logger.info(f"[Apollo STUB] Synthesized contact for {name!r}: {synthesized['email']}")
        return synthesized
