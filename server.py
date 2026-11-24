"""MCP server for the «Умный чат» writing assistant.

The server provides the writing policy and a transparent, rule-based text review.
It does not claim to detect whether a text was written by a human or by AI.
"""

import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

RULES_PATH = Path(__file__).with_name("writing_rules.md")

SERVER_INSTRUCTIONS = """Ты — инструмент «Умный чат», помощник по написанию и редактированию.
Когда пользователь просит написать, переписать, сократить, дополнить или отредактировать
текст, сначала учитывай руководство из get_writing_rules. Сохраняй смысл, жанр,
адресата и индивидуальную манеру автора. Не имитируй ошибки и не обещай обходить
детекторы ИИ. Инструмент review_text — только буквальная проверка заданных паттернов,
а не детектор авторства и не замена смысловой редактуре.
"""

mcp = FastMCP(
    "Умный чат",
    instructions=SERVER_INSTRUCTIONS,
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "8000")),
)


@mcp.tool()
def get_writing_rules() -> str:
    """Return the writing and editing policy used by Умный чат."""
    if not RULES_PATH.exists():
        return "Файл правил не найден на сервере."
    return RULES_PATH.read_text(encoding="utf-8")


@mcp.tool()
def review_text(text: str, genre: str = "auto") -> str:
    """Find selected literal style patterns and return transparent editorial notes.

    This is not an AI detector and does not rewrite the text.
    """
    if not text.strip():
        return "Текст пустой. Пришлите фрагмент для проверки."

    checks = {
        "Шаблонные вступления": [
            "Конечно!", "Отличный вопрос!", "Давайте разберёмся",
            "В современном мире", "На сегодняшний день",
        ],
        "Шаблонные выводы и оговорки": [
            "Подводя итог", "В заключение", "Надеюсь, это поможет",
            "Важно отметить, что", "Стоит учитывать, что",
        ],
        "Рекламные и преувеличенные формулировки": [
            "уникальный опыт", "неповторимая атмосфера", "поворотным моментом",
            "неизгладимый след", "широкий спектр возможностей",
        ],
        "Безличные ссылки на мнения": [
            "эксперты считают", "многие исследователи отмечают",
            "специалисты сходятся во мнении", "ряд источников указывает",
        ],
        "Канцелярит": [
            "в целях осуществления", "в рамках реализации",
            "посредством использования", "на основании вышеизложенного",
            "осуществлять деятельность",
        ],
        "Шаблонная переписка": [
            "Благодарим за обратную связь", "Ваше обращение принято в работу",
            "Надеюсь, у вас всё хорошо",
        ],
        "Плейсхолдеры": [
            "[Имя]", "[Год]", "[Вставить ссылку]", "INSERT_SOURCE_URL",
            "PASTE_URL_HERE", "example.com",
        ],
    }

    lower = text.casefold()
    findings = []
    for label, phrases in checks.items():
        found = [phrase for phrase in phrases if phrase.casefold() in lower]
        if found:
            findings.append(f"{label}: " + "; ".join(found))

    if text.count("—") >= 4:
        findings.append(
            f"Длинные тире: найдено {text.count('—')}; проверьте, не заменяют ли они запятые или точки."
        )
    if text.count("!") >= 4:
        findings.append("Восклицательные знаки: их много; проверьте, оправдана ли такая эмоциональность.")
    if text.count("...") >= 3:
        findings.append("Многоточия: повторяются часто; проверьте, нужны ли все паузы.")

    genre_label = "автоматически" if genre == "auto" else genre
    if findings:
        body = "\n".join(f"- {item}" for item in findings)
    else:
        body = (
            "По встроенному списку точных шаблонов совпадений не найдено. "
            "Это не доказывает естественное происхождение текста и не заменяет редактуру по смыслу."
        )

    return (
        f"Жанр: {genre_label}.\n{body}\n\n"
        "Дополнительно проверьте смысловые повторы, фактическую точность, "
        "соответствие адресату и естественность при чтении вслух. "
        "Полное руководство доступно через get_writing_rules."
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
