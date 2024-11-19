import argparse
import json
import logging
import os
from data_loader import DataLoader
from collections import defaultdict

class QuidProcessor:
    def __init__(self, docsp_data, docfic_data, max_level=10):
        """
        Initialise le processeur Quid avec les données DOCSP et DOCFIC.
        
        :param docsp_data: Liste de dictionnaires contenant les données DOCSP.
        :param docfic_data: Liste de dictionnaires contenant les données DOCFIC.
        :param max_level: Niveau maximal de récursivité.
        """
        self.docsp_data = docsp_data
        self.docfic_data = docfic_data
        self.max_level = max_level
        self.call_graph = {}  # Pour éviter les boucles infinies

        # Prétraitement des données pour créer des index sans doublons
        self.prog_to_subprogs = defaultdict(set)
        for entry in self.docsp_data:
            self.prog_to_subprogs[entry['NOMPROG']].add(entry['NOMSP'])
        
        self.prog_to_files = defaultdict(set)
        for entry in self.docfic_data:
            file_key = (entry['NOMFIC'], entry['TYPOPEN'])
            self.prog_to_files[entry['NOMPROG']].add(file_key)
        
        logging.info("Indexation des données DOCSP et DOCFIC terminée.")

    def find_called_programs(self, program_name, level=0):
        """
        Trouve récursivement les programmes appelés par un programme donné.

        :param program_name: Nom du programme à traiter.
        :param level: Niveau actuel de récursivité.
        :return: Un dictionnaire représentant le programme et ses appels.
        """
        if level > self.max_level:
            logging.warning(f"Maximum recursion level {self.max_level} atteint pour le programme {program_name}.")
            return {"PROGRAM": program_name, "CALLS": []}

        if program_name in self.call_graph:
            logging.warning(f"Programme {program_name} déjà traité. Possibilité de boucle détectée.")
            return {"PROGRAM": program_name, "CALLS": []}

        self.call_graph[program_name] = True

        # Utilisation de l'index pour obtenir les sous-programmes
        called_programs = self.prog_to_subprogs.get(program_name, [])
        calls = []
        for called in called_programs:
            calls.append(self.find_called_programs(called, level + 1))

        return {"PROGRAM": program_name, "CALLS": calls}

    def find_used_files(self, program_name):
        """
        Trouve les fichiers utilisés par un programme donné.

        :param program_name: Nom du programme à traiter.
        :return: Liste de dictionnaires contenant les fichiers utilisés, sans duplication.
        """
        used_files_set = self.prog_to_files.get(program_name, set())
        used_files = [{"NAME": name, "TYPOPEN": typopen} for name, typopen in used_files_set]
        logging.info(f"Programme {program_name} utilise les fichiers: {used_files}")
        return used_files

    def build_json_structure(self, program_name):
        """
        Construit la structure JSON complète pour un programme donné.

        :param program_name: Nom du programme à traiter.
        :return: Dictionnaire représentant la structure JSON.
        """
        structure = self.find_called_programs(program_name)
        self.add_used_files(structure)
        return structure

    def add_used_files(self, structure):
        """
        Ajoute les fichiers utilisés à la structure JSON.

        :param structure: Dictionnaire représentant la structure JSON.
        """
        program = structure['PROGRAM']
        used_files = self.find_used_files(program)
        structure['USED_FILES'] = used_files
        for call in structure['CALLS']:
            self.add_used_files(call)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("quid.log"),
            logging.StreamHandler()
        ]
    )

def main():
    setup_logging()

    parser = argparse.ArgumentParser(description="Quid Data Processor")
    parser.add_argument(
        '-c', '--config',
        type=str,
        default='config.json',
        help='Path to the configuration JSON file.'
    )
    parser.add_argument(
        '-e', '--environment',
        type=str,
        required=True,
        choices=['DEV', 'RE7', 'REF'],
        help='Environment to load data for (DEV, RE7, REF).'
    )
    parser.add_argument(
        '--use-cache',
        action='store_true',
        help='Load data from cache if available.'
    )
    parser.add_argument(
        '-p', '--program',
        type=str,
        required=True,
        help='Name of the program to process.'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Path to the output JSON file.'
    )

    args = parser.parse_args()

    # Charger les données DOCSP et DOCFIC
    data_loader = DataLoader(
        config_path=args.config,
        environment=args.environment,
        use_cache=args.use_cache
    )
    data_loader.load_data()

    # Vérifier si les données ont été chargées
    if not data_loader.docsp_data:
        logging.error("Aucune donnée DOCSP chargée.")
        return
    if not data_loader.docfic_data:
        logging.error("Aucune donnée DOCFIC chargée.")
        return

    # Initialiser le processeur Quid
    processor = QuidProcessor(
        docsp_data=data_loader.docsp_data,
        docfic_data=data_loader.docfic_data
    )

    # Construire la structure JSON
    quid_structure = processor.build_json_structure(args.program)

    # Définir le chemin de sortie
    if args.output:
        output_path = args.output
    else:
        output_path = os.path.join(os.getcwd(), f"{args.program}.json")

    # Sauvegarder le JSON
    try:
        with open(output_path, 'w', encoding='utf-8') as json_file:
            json.dump(quid_structure, json_file, ensure_ascii=False, indent=4)
        logging.info(f"Quid JSON sauvegardé à {output_path}")
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde du JSON: {e}")

if __name__ == "__main__":
    main()
