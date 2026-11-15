
import os
import subprocess
import sys
from pathlib import Path

RULES = ["001", "002", "003", "005", "009", "010", "020"]
BASE_DIR = Path(__file__).resolve().parent

def main():
    errors = []

    for rule in RULES:
        script = BASE_DIR / f"test_rq{rule}.py"
        print(f"\n{'=' * 20} RQ-{rule} {'=' * 20}", flush=True)

        if not script.is_file():
            print(f"ERREUR : fichier absent : {script}", flush=True)
            errors.append(rule)
            continue

        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(BASE_DIR),
            env=os.environ.copy(),
            check=False,
        )

        if result.returncode != 0:
            errors.append(rule)
            print(f"ERREUR TECHNIQUE RQ-{rule}", flush=True)

    print("\n========== BILAN EXECUTION S2 ==========")

    if errors:
        print("Erreurs techniques :", ", ".join(errors))
        return 1

    print("7 scripts executes sans erreur technique.")
    print("Verifier les statuts GO/NO-GO de chaque regle.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
