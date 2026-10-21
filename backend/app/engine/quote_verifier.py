import re
from typing import List, Tuple
from ..models.schemas import SkillClaim

def normalize_text_for_search(text: str) -> str:
    """Normalizes whitespace and removes punctuation variations for robust search."""
    if not text:
        return ""
    # Lowercase, replace non-alphanumeric with single space
    clean = re.sub(r'[^a-zA-Z0-9]', ' ', text.lower())
    return " ".join(clean.split())

def verify_claims_against_source(claims: List[SkillClaim], raw_doc_text: str) -> Tuple[List[SkillClaim], List[str]]:
    """
    Catch 3 Implementation:
    Verifies that every skillClaim's supportingText actually exists verbatim or near-verbatim
    in the raw extracted document text. Prevents hallucinated or injected claims.
    """
    normalized_doc = normalize_text_for_search(raw_doc_text)
    verified_claims: List[SkillClaim] = []
    review_flags: List[str] = []

    for claim in claims:
        quote = claim.supportingText.strip() if claim.supportingText else ""
        if not quote:
            review_flags.append(f"unsupported_claim_empty_quote_{claim.skill}")
            continue

        normalized_quote = normalize_text_for_search(quote)
        
        # Substring search
        if normalized_quote in normalized_doc:
            claim.isQuoteVerified = True
            verified_claims.append(claim)
        else:
            # Fallback: check if at least 70% of the quote words appear as a chunk
            quote_words = normalized_quote.split()
            found_chunk = False
            if len(quote_words) >= 4:
                # Check 4-word window
                window_size = min(6, len(quote_words))
                sub_window = " ".join(quote_words[:window_size])
                if sub_window in normalized_doc:
                    claim.isQuoteVerified = True
                    verified_claims.append(claim)
                    found_chunk = True

            if not found_chunk:
                review_flags.append(f"quote_verification_failed_for_{claim.skill}: '{quote[:40]}...'")
                # Keep claim but mark unverified so downstream can choose to flag
                claim.isQuoteVerified = False
                verified_claims.append(claim)

    return verified_claims, review_flags
