def should_prefragment(*,chunk_text,token_estimate,char_threshold=2250,token_threshold=560):
    chars=len(chunk_text or "")
    tokens=int(token_estimate or 0)
    if chars>=char_threshold:return True,f"chars>={char_threshold}"
    if tokens and tokens>=token_threshold:return True,f"token_estimate>={token_threshold}"
    return False,"canonical-safe"
