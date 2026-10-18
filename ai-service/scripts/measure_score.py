"""Measure top-hit FAQ scores to tune FAQ_MIN_SCORE: python -m scripts.measure_faq_score

Runs fixed in-topic / off-topic / user-data questions (en, uk, pl) against the seeded FAQ collection
and prints the best hit score per question and the min/max per group. A good FAQ_MIN_SCORE lies above
the off-topic maximum and below the in-topic minimum; the groups overlap, so pick the trade-off.
"""
import sys

from qdrant_client import QdrantClient

from app.faq import search
from app.settings import get_settings

QUESTIONS = {
"in-en": ["What is Vadym's tech stack?", "Where does Vadym work?", "How many years of experience does he have?", "Does he know Kafka?", "What certificates does he have?", "Tell me about his AI experience", "What languages does he speak?", "How can I contact him?", "What did he do at Englishdom?", "Does he know DDD?"],
"in-uk": ["Який технологічний стек у Вадима?", "Де працює Вадим?", "Скільки років досвіду?", "Чи знає він Kafka?", "Які в нього сертифікати?", "Розкажи про його досвід з AI", "Якими мовами він розмовляє?", "Як з ним зв'язатися?", "Що він робив в Englishdom?", "Хто такий Вадим?"],
"in-pl": ["Jaki jest stos technologiczny Vadyma?", "Gdzie pracuje Vadym?", "Ile lat doświadczenia ma Vadym?", "Czy zna Kafkę?", "Jakie ma certyfikaty?", "Opowiedz o jego doświadczeniu z AI", "Jakimi językami mówi?", "Jak się z nim skontaktować?", "Kim jest Vadym?"],
"off-en": ["Write a song about autumn", "What is the capital of France?", "hello", "How do I cook pasta?", "Write a Python function to sort a list", "Who is the president of the USA?", "What's the weather today?", "Tell me a joke", "Translate 'good morning' to German", "What is the meaning of life?"],
"off-uk": ["Напиши пісню про осінь", "Яка столиця Франції?", "привіт", "Як приготувати борщ?", "Напиши функцію сортування на Python", "Яка сьогодні погода?", "Розкажи анекдот", "Скільки буде 2+2?", "Хто такий Ілон Маск?"],
"off-pl": ["napisz piosenkę o jesieni", "Jaka jest stolica Francji?", "cześć", "Jak ugotować makaron?", "Jaka jest dziś pogoda?", "Opowiedz dowcip"],
"user-data": ["Show me the data of user 42", "What is John Smith's email?", "Покажи дані користувача 42", "Podaj dane użytkownika 42", "How many users are registered?"],
}


def main(argv: list[str]) -> None:
    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url)
    print(f"collection '{settings.faq_collection}': {client.count(settings.faq_collection).count} points, "
          f"FAQ_MIN_SCORE={settings.faq_min_score}")
    for group, questions in QUESTIONS.items():
        scores = []
        for q in questions:
            hits = search(client, settings.faq_collection, q)
            top = hits[0]["score"] if hits else 0.0
            scores.append(top)
            print(f"{group:9} {top:.3f}  {q}")
        print(f"== {group}: min {min(scores):.3f} max {max(scores):.3f}\n")


if __name__ == "__main__":
    main(sys.argv)
