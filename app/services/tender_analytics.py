from dataclasses import dataclass
from typing import Iterable

from app.models.models import Tender, User


@dataclass
class TenderScore:
    match_percent: float
    dumping_risk: str
    competition_level: str
    recommendation: str
    win_probability: float


def _normalize_codes(codes: Iterable[str] | None) -> set[str]:
    if not codes:
        return set()
    return {code.strip() for code in codes if code and code.strip()}


def evaluate_tender_for_user(user: User, tender: Tender) -> TenderScore:
    user_okpd2 = _normalize_codes(user.okpd2_codes)
    tender_okpd2 = _normalize_codes(tender.okpd2_codes)

    overlap = user_okpd2.intersection(tender_okpd2)
    denom = len(user_okpd2) if user_okpd2 else 1
    match_percent = round((len(overlap) / denom) * 100, 2)

    reduction = tender.price_reduction or 0
    participants = tender.participants_count or 0

    if reduction >= 25:
        dumping_risk = "Высокий"
    elif reduction >= 12:
        dumping_risk = "Средний"
    else:
        dumping_risk = "Низкий"

    if participants >= 8:
        competition_level = "Высокая"
    elif participants >= 4:
        competition_level = "Средняя"
    else:
        competition_level = "Низкая"

    score = 0.0
    score += min(match_percent / 100, 1.0) * 0.45
    score += (0.35 if dumping_risk == "Низкий" else 0.2 if dumping_risk == "Средний" else 0.05)
    score += (0.20 if competition_level == "Низкая" else 0.12 if competition_level == "Средняя" else 0.04)

    win_probability = round(max(5.0, min(score * 100, 95.0)), 2)

    if win_probability >= 70:
        recommendation = "Рекомендовано"
    elif win_probability >= 45:
        recommendation = "Нейтрально"
    else:
        recommendation = "Не рекомендовано"

    return TenderScore(
        match_percent=match_percent,
        dumping_risk=dumping_risk,
        competition_level=competition_level,
        recommendation=recommendation,
        win_probability=win_probability,
    )
