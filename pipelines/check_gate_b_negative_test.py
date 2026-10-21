
# -*- coding: utf-8 -*-
"""
TD AssurConnect - Groupe 04
US-03 : Test negatif de la Gate B

Objectif :
Verifier qu'une modification volontaire dans une copie
de la table Bronze provoque une decision NO-GO.

Table source : crm.type_contrat
Copie testee  : bronze.crm_type_contrat_test

Aucune modification des donnees.
"""

from check_gate_b import verifier_table


def main():

    print("=" * 65)
    print("ASSURCONNECT - GROUPE 04")
    print("US-03 : TEST NEGATIF GATE B")
    print("Batch : S1_G04_001")
    print("=" * 65)

    print("\nControle de la copie modifiee :")

    conforme = verifier_table(
        "crm",
        "type_contrat",
        "crm_type_contrat_test"
    )

    print("\n" + "=" * 65)

    if conforme:
        print("TEST NEGATIF : GO")
        print("ECHEC DU TEST : anomalie non detectee.")
        raise SystemExit(1)

    else:
        print("TEST NEGATIF : NO-GO")
        print("SUCCES DU TEST : anomalie detectee.")

    print("=" * 65)


if __name__ == "__main__":
    main()
