# Tafamidis 관련 키워드 필터링 모듈

TAFAMIDIS_KEYWORDS = [
    'tafamidis',
    'transthyretin',
    'TTR',
    'cardiac amyloidosis',
    '심장 아밀로이드증',
    'Vyndaqel',
    'amyloidosis',
    '아밀로이드'
]

def is_tafamidis_related(text):
    """텍스트에서 Tafamidis 관련 키워드 검색"""
    if not text:
        return False
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in TAFAMIDIS_KEYWORDS)

def filter_tafamidis_items(items, search_fields):
    """
    아이템 리스트에서 Tafamidis 관련 항목만 필터링
    
    Args:
        items: 데이터 리스트
        search_fields: 검색할 필드명 리스트 (예: ['title', 'description'])
    
    Returns:
        필터링된 아이템 리스트
    """
    filtered = []
    for item in items:
        for field in search_fields:
            if is_tafamidis_related(item.get(field, '')):
                filtered.append(item)
                break
    return filtered
