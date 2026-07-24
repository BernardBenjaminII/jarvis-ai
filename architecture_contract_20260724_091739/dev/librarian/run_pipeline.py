from pathlib import Path

from acquisition.pipeline import process

ROOT = Path(
"/media/abdullah/JARVISDATA/Jarvis_Downloaded_Knowledge/staged/mit_targeted/ocw_courses"
)

for course in ROOT.iterdir():

    for z in course.glob("*.zip"):

        metadata, keep = process(z)

        print()

        print("="*60)

        print(course.name)

        print("Metadata files:", metadata.keys())

        print("Useful resources:", len(keep))

        for x in keep[:20]:

            print(" ", x.relative_to(course))
