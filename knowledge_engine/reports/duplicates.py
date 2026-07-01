from pathlib import Path
import csv


def write_duplicates_csv(duplicates, output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "sha256",
            "copies",
            "path"
        ])

        for sha, paths in duplicates.items():
            for path in paths:
                writer.writerow([
                    sha,
                    len(paths),
                    path
                ])


def write_duplicates_markdown(duplicates, output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8") as file:

        file.write("# Duplicate Files\n\n")

        if not duplicates:
            file.write("No duplicates found.\n")
            return

        for sha, paths in duplicates.items():

            file.write("---\n\n")

            file.write(f"## SHA256\n\n`{sha}`\n\n")

            file.write(f"Copies: **{len(paths)}**\n\n")

            for path in paths:
                file.write(f"- {path}\n")

            file.write("\n")
