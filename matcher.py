"""
matcher.py - Two-Stage Deterministic Filtering & Semantic Scheme Ranking Engine
"""
import os
import re
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import schema
import security

# Cache resource placeholder for sentence transformers
_MODEL_CACHE = None

def get_sentence_transformer_model():
    """
    Loads and caches the all-MiniLM-L6-v2 model in memory.
    In Streamlit, this is decorated with @st.cache_resource in app.py.
    """
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    try:
        from sentence_transformers import SentenceTransformer
        try:
            # Try loading from local cache first to avoid network calls
            _MODEL_CACHE = SentenceTransformer('all-MiniLM-L6-v2', local_files_only=True)
            return _MODEL_CACHE
        except Exception:
            _MODEL_CACHE = SentenceTransformer('all-MiniLM-L6-v2')
            return _MODEL_CACHE
    except Exception as e:
        print(f"Warning: Could not load sentence-transformers: {e}. Falling back to TF-IDF.")
        return None

def compute_keyword_similarity(query_text: str, corpus_texts: List[str]) -> np.ndarray:
    """
    Lightweight fallback for low-bandwidth mode or when sentence-transformers is loading.
    Computes TF-IDF cosine similarity.
    """
    if not query_text.strip() or not corpus_texts:
        return np.zeros(len(corpus_texts))
    try:
        vectorizer = TfidfVectorizer(stop_words='english', token_pattern=r'(?u)\b\w+\b')
        all_docs = [query_text] + corpus_texts
        tfidf_matrix = vectorizer.fit_transform(all_docs)
        sims = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]
        return np.clip(sims, 0.0, 1.0)
    except Exception:
        return np.zeros(len(corpus_texts))

def compute_embedding_similarity(model, query_text: str, corpus_texts: List[str]) -> np.ndarray:
    """
    Computes dense semantic cosine similarity using sentence-transformers.
    """
    if model is None or not query_text.strip() or not corpus_texts:
        return compute_keyword_similarity(query_text, corpus_texts)
    try:
        q_emb = model.encode([query_text], convert_to_numpy=True, normalize_embeddings=True)
        doc_embs = model.encode(corpus_texts, convert_to_numpy=True, normalize_embeddings=True)
        sims = np.dot(doc_embs, q_emb.T).flatten()
        # Scale range [-1, 1] to [0, 1]
        sims = np.clip((sims + 1.0) / 2.0, 0.0, 1.0)
        return sims
    except Exception as e:
        print(f"Embedding computation error: {e}. Using TF-IDF fallback.")
        return compute_keyword_similarity(query_text, corpus_texts)

def generate_qualification_reasons(user_profile: Dict[str, Any], scheme: Dict[str, Any]) -> List[str]:
    """
    Generates plain-language explainability bullet points detailing why
    the applicant satisfies each specific rule.
    """
    reasons = []
    
    # 1. Category explainability
    user_cat = user_profile.get('category', '')
    scheme_cats = schema.parse_multi_field(scheme.get('category', ''))
    if 'All' in scheme_cats:
        reasons.append(f"**Universal Social Inclusion**: Open to all social categories including **{user_cat}**.")
    elif user_cat in scheme_cats:
        reasons.append(f"**Targeted Category Match**: Specifically mandates priority allocation for **{user_cat}** entrepreneurs.")
        
    # 2. Gender explainability
    user_gender = user_profile.get('gender', 'All-Any')
    scheme_genders = schema.parse_multi_field(scheme.get('eligible_gender', ''))
    if user_gender == 'Female' and 'Female' in scheme_genders:
        reasons.append("**Women Empowerment Focus**: Provides concessional interest rebate / dedicated quota for women founders.")
    elif 'All' in scheme_genders:
        reasons.append("**Gender Neutral Eligibility**: Accommodates all eligible gender identities.")
        
    # 3. Income explainability
    try:
        user_inc = int(user_profile.get('income', 0))
        max_inc = int(scheme.get('max_income', -1))
        if max_inc == -1:
            reasons.append("**No Income Ceiling**: Accessible regardless of family income bracket.")
        elif user_inc <= max_inc:
            reasons.append(f"**Income Within Limits**: Your annual family income (₹{user_inc:,.0f}) is within the cap of ₹{max_inc:,.0f}.")
    except Exception:
        pass
        
    # 4. Age explainability
    try:
        user_age = int(user_profile.get('age', 25))
        min_age = int(scheme.get('min_age', 18))
        max_age = int(scheme.get('max_age', 70))
        if min_age <= user_age <= max_age:
            reasons.append(f"**Age Qualification**: Applicant age ({user_age} years) is within the eligible range ({min_age}–{max_age} years).")
    except Exception:
        pass
        
    # 5. PwD / Divyangjan explainability
    is_pwd = user_profile.get('is_pwd', False)
    pwd_only = schema.parse_bool(scheme.get('pwd_only', False))
    if is_pwd:
        if pwd_only:
            reasons.append("**Dedicated Divyangjan Support**: 100% reserved for certified Persons with Disabilities.")
        else:
            reasons.append("**Special Category Preference**: PwD entrepreneurs receive prioritized processing & subsidy benefits.")
            
    # 6. Sector explainability
    user_sector = user_profile.get('sector', 'All')
    scheme_sectors = schema.parse_multi_field(scheme.get('sector', ''))
    if user_sector != 'All' and (user_sector in scheme_sectors or 'All' in scheme_sectors):
        reasons.append(f"**Sector Compatibility**: Supports your chosen domain of **{user_sector}**.")
        
    # 7. State coverage
    user_state = user_profile.get('state', 'All India')
    scheme_states = schema.parse_multi_field(scheme.get('states', ''))
    if 'All India' in scheme_states:
        reasons.append(f"**Nationwide Coverage**: Available across all districts of **{user_state}**.")
    elif user_state in scheme_states:
        reasons.append(f"**State-Specific Implementation**: Operates actively in **{user_state}**.")
        
    return reasons

def match_schemes(
    user_profile: Dict[str, Any],
    schemes_df: pd.DataFrame,
    embedding_model=None,
    low_bandwidth_mode: bool = False
) -> List[Dict[str, Any]]:
    """
    Two-Stage matching pipeline:
    Stage 1: Deterministic Boolean Filter (Zero eval/exec, pure vectorized & row-level filtering)
    Stage 2: Semantic Similarity Scoring & Explainability Generation
    """
    if schemes_df.empty:
        return []
        
    # Extract & sanitize user parameters
    user_category = security.sanitize_text(user_profile.get('category', 'All'))
    user_gender = security.sanitize_text(user_profile.get('gender', 'All-Any'))
    is_pwd = bool(user_profile.get('is_pwd', False))
    pwd_percent = int(user_profile.get('pwd_percent', 0))
    user_income = int(user_profile.get('income', 0))
    user_age = int(user_profile.get('age', 30))
    user_state = security.sanitize_text(user_profile.get('state', 'All India'))
    user_sector = security.sanitize_text(user_profile.get('sector', 'All'))
    business_need = security.sanitize_text(user_profile.get('business_need', ''))
    
    # -------------------------------------------------------------
    # STAGE 1: Deterministic Boolean Filtering
    # -------------------------------------------------------------
    surviving_indices = []
    
    for idx, row in schemes_df.iterrows():
        # A. Category check
        scheme_cats = schema.parse_multi_field(row.get('category', ''))
        cat_match = False
        if 'All' in scheme_cats or user_category in ('All', '') or user_category in scheme_cats:
            cat_match = True
        # EWS / General mapping
        elif user_category == 'EWS' and ('General' in scheme_cats or 'EWS' in scheme_cats):
            cat_match = True
        if not cat_match:
            continue
            
        # B. Gender check
        scheme_genders = schema.parse_multi_field(row.get('eligible_gender', ''))
        gender_match = False
        if user_gender in ('All-Any', 'All', '') or 'All' in scheme_genders or user_gender in scheme_genders:
            gender_match = True
        if not gender_match:
            continue
            
        # C. PwD check
        pwd_only = schema.parse_bool(row.get('pwd_only', False))
        if pwd_only:
            if not is_pwd or pwd_percent < 40:
                continue
                
        # D. Income check
        try:
            max_inc = int(row.get('max_income', -1))
            min_inc = int(row.get('min_income', 0))
            if max_inc != -1 and user_income > max_inc:
                continue
            if user_income < min_inc:
                continue
        except (ValueError, TypeError):
            pass
            
        # E. Age check
        try:
            min_age = int(row.get('min_age', 18))
            max_age = int(row.get('max_age', 70))
            if user_age < min_age or user_age > max_age:
                continue
        except (ValueError, TypeError):
            pass
            
        # F. State check
        scheme_states = schema.parse_multi_field(row.get('states', ''))
        if user_state not in ('All India', '') and 'All India' not in scheme_states and user_state not in scheme_states:
            continue
            
        # G. Sector check
        scheme_sectors = schema.parse_multi_field(row.get('sector', ''))
        if user_sector not in ('All', '') and 'All' not in scheme_sectors and user_sector not in scheme_sectors:
            continue
            
        surviving_indices.append(idx)
        
    if not surviving_indices:
        return []
        
    surviving_df = schemes_df.loc[surviving_indices].copy()
    
    # -------------------------------------------------------------
    # STAGE 2: Semantic Ranking & Scoring
    # -------------------------------------------------------------
    corpus_descriptions = [
        f"{r.get('scheme_name', '')}. {r.get('description', '')}. Sector: {r.get('sector', '')}. Benefit: {r.get('benefit_amount', '')}"
        for _, r in surviving_df.iterrows()
    ]
    
    if business_need.strip():
        if low_bandwidth_mode or embedding_model is None:
            sim_scores = compute_keyword_similarity(business_need, corpus_descriptions)
        else:
            sim_scores = compute_embedding_similarity(embedding_model, business_need, corpus_descriptions)
    else:
        # If no custom business description provided, assign balanced baseline
        sim_scores = np.full(len(surviving_df), 0.75)
        
    results = []
    
    for i, (orig_idx, row) in enumerate(surviving_df.iterrows()):
        scheme_dict = row.to_dict()
        base_sim = float(sim_scores[i])
        
        # Calculate composite match score
        # Deterministic eligibility grants 70% base score + up to 30% semantic affinity
        subsidy_pct = float(row.get('subsidy_percentage', 0.0))
        subsidy_bonus = min(subsidy_pct * 0.05, 5.0)  # Up to 5% bonus for capital subsidies
        
        raw_pct = (70.0 + (base_sim * 25.0) + subsidy_bonus)
        match_percentage = int(np.clip(raw_pct, 65, 99))
        
        reasons = generate_qualification_reasons(user_profile, scheme_dict)
        docs = schema.parse_multi_field(scheme_dict.get('required_documents', ''))
        
        # Validate URL safely
        is_safe_url, safe_url = security.validate_url(scheme_dict.get('official_url', ''))
        
        results.append({
            'scheme_id': scheme_dict.get('scheme_id', ''),
            'scheme_name': scheme_dict.get('scheme_name', ''),
            'sponsoring_body': scheme_dict.get('sponsoring_body', ''),
            'match_score': match_percentage,
            'benefit_type': scheme_dict.get('benefit_type', 'Loan'),
            'benefit_amount': scheme_dict.get('benefit_amount', ''),
            'subsidy_percentage': subsidy_pct,
            'description': scheme_dict.get('description', ''),
            'required_documents': docs,
            'official_url': safe_url if is_safe_url else '',
            'url_is_safe': is_safe_url,
            'contact_info': scheme_dict.get('contact_info', ''),
            'qualification_reasons': reasons,
            'sector': scheme_dict.get('sector', ''),
            'category': scheme_dict.get('category', '')
        })
        
    # Sort descending by match score
    results.sort(key=lambda x: x['match_score'], reverse=True)
    return results

def aggregate_document_checklist(matched_schemes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregates required documents across top matched schemes with mapping of
    which schemes require which document.
    """
    doc_mapping = {}
    for s in matched_schemes:
        sname = s['scheme_name']
        for doc in s['required_documents']:
            doc = doc.strip()
            if not doc:
                continue
            if doc not in doc_mapping:
                doc_mapping[doc] = []
            doc_mapping[doc].append(sname)
            
    checklist = []
    for doc, schemes in doc_mapping.items():
        checklist.append({
            'document_name': doc,
            'required_by_count': len(schemes),
            'required_by_schemes': schemes
        })
        
    # Sort by necessity count
    checklist.sort(key=lambda x: x['required_by_count'], reverse=True)
    return checklist
