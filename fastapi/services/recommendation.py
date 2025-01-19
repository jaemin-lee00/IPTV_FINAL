from services.youtube import search_youtube_videos, get_video_details
from services.similarity import calculate_similarity_tfidf, calculate_similarity_nlp

CATEGORY_KEYWORDS = {
    "수면장애": ["불규칙적 수면 패턴", "잠 잘 드는 꿀팁"],
    "심혈관질환": ["가슴통증", "간단한 운동"],
    "당뇨": ["심한 식곤증", "식단 관리"],
    "간암": ["임상이 피로", "과도한 음주"],
    "폐암": ["잦은 기침", "잦은 흡연"]
} # 하나만

YOUTUBE_SEARCH_KEYWORDS = {
    "불규칙적 수면 패턴": ["수면장애"],
    "잠 잘 드는 꿀팁": ["불면증", "예방"],
    "가슴통증": ["심혈관 질환", "증상"],
    "간단한 운동": ["노인", "간단한 운동"],
    "심한 식곤증": ["당뇨", "식곤증"],
    "식단 관리": ["혈당관리", "식단"],
    "임상이 피로": ["간암", "피로"],
    "과도한 음주": ["간", "음주"],
    "잦은 기침": ["폐암", "기침"],
    "잦은 흡연": ["폐", "기침"]
}

def recommend_videos(categories):
    # 사용자 카테고리에 따라 키워드 생성
    keywords = []
    for category in categories:
        if category in CATEGORY_KEYWORDS:
            keywords.extend(CATEGORY_KEYWORDS[category])

    search_keywords = []
    for keyword in keywords:
        if keyword in YOUTUBE_SEARCH_KEYWORDS:
            search_keywords.extend(YOUTUBE_SEARCH_KEYWORDS[keyword])

    # YouTube 검색 및 유사도 계산
    search_results = search_youtube_videos(search_keywords)
    video_ids = [item["id"]["videoId"] for item in search_results]
    video_details = get_video_details(video_ids)

    texts = [video["snippet"]["title"] + " " + video["snippet"]["description"] for video in video_details]
    tfidf_scores = calculate_similarity_tfidf(texts, search_keywords)
    nlp_scores = calculate_similarity_nlp(texts, search_keywords)

    # 점수 계산 및 정렬
    recommendations = []
    for i, video in enumerate(video_details):
        recommendations.append({
            "title": video["snippet"]["title"],
            "link": f"https://www.youtube.com/watch?v={video['id']}",
            "score": 0.5 * tfidf_scores[i] + 0.5 * nlp_scores[i]
        })
    return sorted(recommendations, key=lambda x: x["score"], reverse=True)
