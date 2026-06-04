"""Generate 32-line ASCII art files for examine/sheet."""
from __future__ import annotations

import os

ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "data", "art")


def portrait(label: str, face_line: str, body_lines: list[str]) -> list[str]:
    w = 34
    h = 32
    lines: list[str] = []
    for y in range(h):
        if y in (0, h - 1):
            lines.append("+" + "-" * (w - 2) + "+")
        elif y == 1:
            t = f" {label} ".center(w - 2)[: w - 2]
            lines.append("|" + t.ljust(w - 2) + "|")
        elif y == 2:
            lines.append("|" + " " * (w - 2) + "|")
        elif y < 10:
            s = face_line.center(w - 2)[: w - 2]
            lines.append("|" + s.ljust(w - 2) + "|")
        elif y < 22:
            idx = y - 10
            s = body_lines[idx % len(body_lines)].center(w - 2)[: w - 2] if body_lines else ""
            lines.append("|" + s.ljust(w - 2) + "|")
        else:
            lines.append("|" + " " * (w - 2) + "|")
    return lines


def write(rel: str, art_lines: list[str], desc: str) -> None:
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(art_lines) + "\n---\n" + desc + "\n")


def main() -> None:
    face = [
        "      .---.      ",
        "     /  O  \\     ",
        "    |   |   |    ",
        "     \\  -  /     ",
    ]
    body = [
        "    /|     |\\    ",
        "     |  #  |     ",
        "    / \\   / \\    ",
        "   /   V   \\   ",
        "  |    |    |  ",
        "  |    |    |  ",
        "   \\  / \\  /   ",
        "    \\/   \\/    ",
    ]
    write(
        "characters/elion_portrait.txt",
        portrait("ЭЛИОН", face[1], face + body),
        "Элион — хранитель увядшего святилища.\nИщет последнюю искру Лиры.\nПепел осел на плечах, но он всё ещё идёт.",
    )
    write(
        "characters/elder_portrait.txt",
        portrait("СТАРЕЙШИНА", "     /\\_/\\     ", ["    ( o.o )    ", "     | ^ |     ", "    /|   |\\    ", "     |   |     ", "    _|   |_    "]),
        "Старейшина пепла помнит зелёную траву.\nНаучит слушать — не только сражаться.",
    )

    herb: list[str] = []
    for y in range(32):
        if y in (0, 31):
            herb.append("+" + "-" * 32 + "+")
        elif y == 1:
            herb.append("|" + "   СЕРАЯ ТРАВА ПЕПЛА   ".center(32)[:32] + "|")
        else:
            row = "".join("o" if (x + y) % 5 == 0 else ("." if (x * y + y) % 7 else ",") for x in range(32))
            herb.append("|" + row[:32] + "|")
    write("materials/grey_herb_large.txt", herb, "Серая трава впитывает пепел ветра.\nМожно собрать клавишей E.")

    forge: list[str] = []
    for y in range(32):
        if y in (0, 31):
            forge.append("+" + "-" * 32 + "+")
        elif y == 1:
            forge.append("|" + "      КУЗНЯ ПЕПЛА       ".center(32)[:32] + "|")
        elif 8 <= y <= 24:
            if y == 12:
                inner = "    [####]    "
            elif y == 16:
                inner = "    | ~~ |    "
            elif 10 <= y <= 22:
                inner = "    | ## |    "
            else:
                inner = "              "
            forge.append("|" + inner.center(32)[:32] + "|")
        else:
            forge.append("|" + " " * 32 + "|")
    write("materials/ash_forge.txt", forge, "Кузня Пепла ждёт материалов.\nE — открыть крафт.")

    write(
        "enemies/sorrow_large.txt",
        portrait("СКОРБЬ-ИСКРА", "     *·*·*     ", ["    \\  |  /    ", "     . . .     ", "    ~  ~  ~    ", "   (       )   "]),
        "Скорбь-искра — осколок чужой памяти.\nМожно пощадить, если слушать.",
    )
    print("Generated large art files in", ROOT)


if __name__ == "__main__":
    main()
