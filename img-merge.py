import os

pwd = os.getcwd()
all_files = []
for root, dirs, files in os.walk(pwd):
    clean = []
    for f in files:
        if f != "extracted":
            clean.append(f)
    all_files.append((root, clean))

concated_directory = os.path.join(pwd, "0a-image-concated")
os.makedirs(concated_directory, exist_ok=True)

for root, files in all_files:
    prefix = (
        os.path.relpath(root, pwd)
        .replace("/", "_")
        .encode("utf-8", "ignore")
        .decode("utf-8")
    )
    for file in files:
        current = os.path.relpath(os.path.join(root, file), concated_directory)
        concate = os.path.join(concated_directory, f"{prefix}_{file}")
        if not os.path.exists(concate):
            os.symlink(current, concate)
print(f"save to {concated_directory}")
