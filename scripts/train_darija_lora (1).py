"""Fine-tune an instruction model on the Darija chat dataset with QLoRA.

This script has two modes:

1. Dataset generation (no GPU needed):
     python scripts/train_darija_lora.py --generate-dataset \
         --generate-count 1000 \
         --generate-output docs/darija_marocaine_latin_10000.jsonl

   This writes a synthetic JSONL dataset of Darija (Moroccan Arabic, Latin
   script) conversations, following the same `messages` schema expected by
   the training step below (system/user/assistant turns).

2. Training (run on a Linux NVIDIA GPU host):
     python scripts/train_darija_lora.py --dataset docs/darija_marocaine_latin_10000.jsonl

The output of training is a PEFT adapter, not a copy of the full base model.
This keeps the artifact small and makes the base model used for inference
explicit.
"""

from __future__ import annotations

import argparse
import itertools
import json
import random
from pathlib import Path

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, help="JSONL with an OpenAI-style `messages` field")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/darija-lora"))
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--max-seq-length", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--gradient-accumulation", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--seed", type=int, default=42)

    # --- dataset generation mode ---
    parser.add_argument(
        "--generate-dataset",
        action="store_true",
        help="Generate a synthetic Darija conversations dataset instead of training.",
    )
    parser.add_argument(
        "--generate-count",
        type=int,
        default=1000,
        help="Number of conversations to generate (default: 1000).",
    )
    parser.add_argument(
        "--generate-output",
        type=Path,
        default=Path("docs/darija_marocaine_latin_10000.jsonl"),
        help="Where to write the generated JSONL dataset.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Dataset generation: synthetic Darija (Moroccan Arabic, Latin script) chats
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = "Nta Brainy, mou3awine dki chatbot li kay-hder Darija maghribiya m3a l'mosta3milin."

VILLES = [
    "Casablanca", "Rabat", "Marrakech", "Fes", "Tanger", "Agadir", "Oujda",
    "Tetouan", "Meknes", "Kenitra", "Safi", "El Jadida", "Nador", "Beni Mellal",
    "Khouribga", "Settat", "Essaouira", "Chefchaouen", "Ouarzazate", "Errachidia",
    "Ifrane", "Al Hoceima", "Larache", "Taza", "Sale", "Mohammedia", "Khemisset",
    "Taroudant", "Guelmim", "Laayoune",
]

PLATS = [
    "tagine dyal lham", "couscous", "harira", "rfissa", "tanjia", "pastilla",
    "briouates", "seffa", "zaalouk", "bissara", "kefta", "chebakia", "sellou",
    "tagine dyal l7out", "msemen", "baghrir", "harcha", "makouda", "batbout",
    "tagine dyal khodra",
]

MATIERES = [
    "les maths", "la physique", "l'anglais", "la chimie", "l'informatique",
    "l'histoire", "la biologie", "l'arabe", "l'economie", "le francais",
    "la geographie", "la programmation", "les statistiques", "la philosophie",
]

PRODUITS = [
    "smartphone", "laptop", "sac", "chaussures", "jelaba", "montre", "tele",
    "frigo", "table", "kaskita", "sac dial l'ecole", "printer", "casque",
    "chargeur", "batterie externe",
]

TECH_ISSUES = [
    "l'application katsedd b'blasa", "l'internet dyali khayeb bezaf",
    "batri dyal telephone kat-salle bzarba", "ma qadch ndir update l'app",
    "l'appli katqol erreur mnin kanhawel ndkhol", "ma khdmach l wifi f dar",
    "ma9dertch nrecuperi kelmat sser dyali", "l'application 3aitat bzaf",
    "ma bghatch tetsajjel l'appli", "screen dyal telephone khessarat",
]

SPORT_EQUIPES = [
    "Raja", "Wydad", "l'equipe nationale dyal Maghrib", "FUS Rabat",
    "Hassania Agadir", "MAS Fes", "Ittihad Tanger", "RSB Berkane",
]

TERMES = [
    "l'intelligence artificielle", "le cloud", "la blockchain", "un algorithme",
    "le machine learning", "un serveur", "une API", "le wifi", "la 5G",
    "un antivirus", "la crypto-monnaie", "le big data",
]

MOTS_TRADUCTION = [
    ("hello", "salam / ahlan"), ("thank you", "choukran"), ("please", "3afak"),
    ("goodbye", "bslama"), ("friend", "sahbi / sahebti"), ("today", "lyoum"),
    ("tomorrow", "ghedda"), ("water", "lma"), ("food", "makla"),
    ("beautiful", "zwina / zwin"), ("work", "khedma"), ("house", "dar"),
    ("family", "3aila"), ("money", "flouss"), ("time", "waqt"),
]

DOCS_ADMIN = [
    "CIN", "passeport", "carte grise", "permis dial sya9a", "acte dial naissance",
    "carte sejour", "casier judiciaire",
]

WELLNESS_TOPICS = [
    ("n3ass mzyan", "tri9 bach t7esen l3adat dyal noum"),
    ("nchreb lma bezaf", "shi 8 koussan f nhar"),
    ("nwelli aktif", "chi mchya saghira kol nhar"),
    ("ndir stress moins", "ta9niyat dyal tanaffos w rahat"),
    ("nakol mezyan", "moukhtalaf makla f wa9tou"),
]

GREETING_OPENERS = ["Salam", "Ahlan", "Sbah lkhir", "Msa lkhir", "Salam 3lik"]
NAMES = ["Yassine", "Sara", "Omar", "Imane", "Rida", "Fatima", "Adil", "Hind", "Anas", "Nour"]


def _combo(user_templates, assistant_templates, slots):
    """Cross user/assistant templates with slot values that share {slot}."""
    out = []
    for u_tpl, a_tpl in itertools.product(user_templates, assistant_templates):
        for slot in slots:
            out.append((u_tpl.format(slot=slot), a_tpl.format(slot=slot)))
    return out


def build_greetings():
    users = ["{opener}, kifach nta labas?", "{opener} khouya, wach kolshi mzyan?", "{opener}, chno khbarek lyoum?"]
    assistants = [
        "Wa 3lik salam! Ana bikhir hmdullah, chnou ymkn n3awnek fih lyoum?",
        "Ahlan bik! Kolshi mzyan, ana hna bach n3awnek f ay haja bghiti.",
        "Labas 3lik hmdullah! Golli chno 3andek bach ndiro lih chi haja.",
    ]
    out = []
    for opener, name in itertools.product(GREETING_OPENERS, NAMES):
        u = random.Random(hash((opener, name)) & 0xFFFF).choice(users).format(opener=opener)
        a = random.Random(hash((name, opener)) & 0xFFFF).choice(assistants)
        out.append((f"{u} (ana {name}.)", a))
    return out


def build_weather():
    users = ["Chno l'jaw f {slot} lyoum?", "Wach ghadi tnzel chta f {slot}?", "Kifach l'jaw ghadi ykoun f {slot} had s'imana?"]
    assistants = [
        "Ma3andich accès l'informations dyal l'jaw en temps reel, walakin ymkn lik tchouf app dial météo bach t3araf l'jaw dyal {slot} bdi9a.",
        "Bach ta3raf l'jaw dyal {slot} b dakika, khasek t consulti chi site dial météo, ana ma9dertch nakhod données live.",
    ]
    return _combo(users, assistants, VILLES)


def build_recipes():
    users = ["Kifach ndir {slot}?", "3tini recette dyal {slot} bach ndirha f dar.", "Bghit nta3lam ndir {slot}, mnin nbda?"]
    assistants = [
        "Bach ddir {slot}, khasek t7der l'ingredients l'oula, mba3d tbda tayr dial mokawinat bshwiya bshwiya 3la nar mtowassta hta ytebl mzyan.",
        "Recette dyal {slot} basita: hder l7wayj, khalt l'mokawinat, khalihom yetblou 3la nar hadya, w dwez chi 3adat dyal l3ayla dyalek.",
    ]
    return _combo(users, assistants, PLATS)


def build_travel():
    users = ["Ach khassni nzour f {slot}?", "3tini chi idées dyal blayes fin ymkn nmchi f {slot}.", "Kifach njib rihla mzyana f {slot}?"]
    assistants = [
        "F {slot}, ymkn tzour l'blayes l'mashhoura, tjrreb makla lokale, w t'akhod wa9tek bach tchouf souk w monuments dyal l'medina.",
        "Bach ndir rihla mzyana f {slot}, khtar fondouk qrib mn centre, dir programme fih blayes touristiques w wa9t dyal rahat.",
    ]
    return _combo(users, assistants, VILLES)


def build_shopping():
    users = ["Fin ymkn nshri {slot} b taman mzyan?", "Chno khasni na3ref 9bel ma nshri {slot}?", "3tini nasiha 9bel ma nshri {slot}."]
    assistants = [
        "Bach tshri {slot} b taman mzyan, 9aren l'asaman f blassa wla f l'internet, w chouf l'avis dyal nas li chraw 9bel.",
        "9bel ma techri {slot}, ta2akad mn jouda dyalha w garantie, w khtar l'markiz li 3andou service après-vente.",
    ]
    return _combo(users, assistants, PRODUITS)


def build_tech_support():
    users = ["{slot}, chno ndir?", "3andi mochkil: {slot}. 3awnni 3afak.", "Ma3reftch nhal mochkil dyal {slot}."]
    assistants = [
        "Bach thal mochkil dyal '{slot}', jarreb 9bel kolchi t3awd tshaghal l'appareil (redémarrage), mba3d chouf update jdid.",
        "L mochkil dyal '{slot}' ghalban ykoun m3lqa m3a connexion wla version qdima, jarreb tmsah cache w t3awd installation.",
    ]
    return _combo(users, assistants, TECH_ISSUES)


def build_school():
    users = ["Ach ymkn ndir bach nfhem mezyan {slot}?", "3tini tips bach ntkoun mzyan f {slot}.", "Kifach nraja3 {slot} b tari9a mzyana?"]
    assistants = [
        "Bach tfhem {slot} mzyan, 9assem l'wa9t dyalek, dir tamarine daymen, w khdem m3a majmou3a dyal zohor bach tshrahou l ba3diyathom.",
        "L tari9a l'mzyana f {slot} hiya nta9is exercices katbdaw men shwiya lel s3ib, w daymen tsawel mnin ma tfhemtich.",
    ]
    return _combo(users, assistants, MATIERES)


def build_wellness():
    users = ["Bghit {slot}, chno ymkn ndir?", "3tini nasa2i7 bach {slot}."]
    assistants = ["Bach {slot}, 3andek {advice}.", "Wahd tari9a mzyana bach {slot} hiya {advice}."]
    out = []
    for topic, advice in WELLNESS_TOPICS:
        for u_tpl in users:
            for a_tpl in assistants:
                out.append((u_tpl.format(slot=topic), a_tpl.format(slot=topic, advice=advice)))
    return out


def build_work():
    topics = ["ndir CV mzyan", "nnjah f entretien d'embauche", "nl9a khedma jdida", "nkteb lettre de motivation"]
    users = ["3awnni {slot}.", "3tini nasiha bach {slot}."]
    assistants = [
        "Bach {slot}, khasek tebda b ta7did l'objectif dyalek, mba3d dir liste dyal l'khbra w l'moukhtassat li 3andek.",
        "Nasiha dyali bach {slot}: kon dqi9 f kelmat dyalek, w wri l'amthila mlmousa dyal shghol li dertihom.",
    ]
    return _combo(users, assistants, topics)


def build_entertainment():
    users = ["3tini idée dyal film ymkn nchouf lyoum.", "Chno ymkn ndir bach ntfarraj lyoum?"]
    assistants = [
        "Ymkn tchouf chi film comedie wla drame bhal l goutek, wla t7wess 3la chi wthaiqi f domaine li 3ajbek.",
        "Jarreb chi série jdida wla musica jdida, wla tema3 m3a chi sahbek chi laqa2 mzyan.",
    ]
    out = []
    for u, a in itertools.product(users, assistants):
        out.append((u, a))
    return out * 8  # small pool duplicated with tiny variation later


def build_sports():
    users = ["Chno rayek f {slot}?", "3tini ra2yek 3la niveau dyal {slot} had l'mawssim."]
    assistants = [
        "{slot} 3andha jomhour kbir w tarikh twil, walakin ma3andich données live 3la nataij dyalha dork.",
        "Bach t3araf hala dyal {slot} b dakika, khasek tchouf chi site sportif rasmi.",
    ]
    return _combo(users, assistants, SPORT_EQUIPES)


def build_definitions():
    users = ["Chno houwa {slot}?", "Fasser liya {slot} b tari9a sahla."]
    assistants = [
        "{slot} houwa mafhoum tiqni li kaydir 3la maloumat wla technologia mo3ayna, w kayet2sta3mal bezaf f domain dyal technologie.",
        "B tari9a sahla, {slot} ymkn nfahmouh bhal wahd l'ada wla technologie li kate3awen f automatisation w tahlil dyal ma3lomat.",
    ]
    return _combo(users, assistants, TERMES)


def build_translation():
    users = ["Kifach nqal '{slot0}' b darija?", "Chno hiya tarjama dyal '{slot0}' b darija?"]
    assistants = ["'{slot0}' b darija kaygoulou lha: {slot1}."]
    out = []
    for mot, tarjama in MOTS_TRADUCTION:
        for u_tpl in users:
            for a_tpl in assistants:
                out.append((u_tpl.format(slot0=mot), a_tpl.format(slot0=mot, slot1=tarjama)))
    return out


def build_admin():
    users = ["Chno khassni ndir bach njib {slot}?", "3tini l khtawat bach njdd {slot}."]
    assistants = [
        "Bach tjib {slot}, khasek tmchi l'jama3a wla l'idara l'mokhtassa, w tjib les documents li matloubin, w tt2aked mn service.gov.ma.",
        "Njjad dyal {slot} kaytlab dossier khass, khasek tchouf site rasmi wla mktb l'moukhtass bach t3araf l'khtawat b dakika.",
    ]
    return _combo(users, assistants, DOCS_ADMIN)


def build_environment():
    topics = ["nrecycle zbel dyalna", "n9elslou stir9a dyal l'ma", "n9elslou stir9a dyal l'kahraba", "nhafdou 3la l'bi2a"]
    users = ["Kifach ymkn ndir bach {slot}?", "3tini idées bach {slot}."]
    assistants = [
        "Bach {slot}, bda b khtawat sghar: fassel zbel, 9elles stir9a dyal l'ma f dar, w khdem b energies renouvelables ila mkin.",
        "Idea mzyana bach {slot} hiya twali t3awd t2amel l'blastik w t9ess l'jihaz li kaykhdmo b kahraba mnin ma khassekch.",
    ]
    return _combo(users, assistants, topics)


def build_jokes():
    pairs = [
        ("Golli chi nokta bach nedhak.", "Wahed rajel qal l sahbou: 'Kant 3andi khedma f banque, walakin trad l'khedma... mabghawnich nban mzyan m3a nas!' Hhh."),
        ("3andek chi nokta khafifa?", "Chi wahed qal: 'Ana ma3andi wa9t bach nrou7 l'gym, walakin 3andi wa9t bzaf bach nfker fach ghadi nrou7!'"),
        ("Dhikni b chi haja mdhika.", "Chi wahed qal l tabib: 'Doctor, kolla nharrek 3la l'internet nssa smiti!' Tabib jawbou: 'Rah houwa hadchi li kaywe93 fach ma3andkch mot de passe.'"),
    ]
    return pairs * 12


def build_motivation():
    users = ["Bghit chi kelma dyal encouragement.", "3tini motivation bach nkml khedmti.", "Chd 3lia bach nkml li bda dyali."]
    assistants = [
        "Kol khtwa sghira katqarbek l l'hadaf lkbir, sir 9dam w matwaqqafch, nta 9ader!",
        "L'moukoula f had l'mochkil hiya l'istimrariya, dwam m3a nafsek b sabre w ghadi twsel.",
        "Ma tensach chhal drti mn tri9, kml b nafss l'himma li bditi biha.",
    ]
    out = []
    for u, a in itertools.product(users, assistants):
        out.append((u, a))
    return out * 6


def build_transport():
    users = ["Kifach nwsel l {slot} b transport public?", "Chno houma l'khyarat dyal transport bach nmchi l {slot}?"]
    assistants = [
        "Bach twsel l {slot}, ymkn tsta3mel taxi, bus, wla tren ila kayn, w hssen tchouf horaires 9bel ma tkhrej.",
        "L'khyarat bach tmchi l {slot} kaykhtalfou hssab l masafa, jrreb app dyal transport bach t3araf a7san tari9a.",
    ]
    return _combo(users, assistants, VILLES)


def build_homework_math():
    problems = [(a, b) for a in range(2, 12) for b in range(2, 12)]
    users = ["Chhal howa {slot0} + {slot1}?", "3awnni nhssab {slot0} khrb {slot1}."]
    out = []
    for a, b in problems:
        add = a + b
        mul = a * b
        out.append((f"Chhal howa {a} + {b}?", f"{a} + {b} kaysawi {add}."))
        out.append((f"3awnni nhssab {a} khrb {b}.", f"{a} khrb {b} (يعني {a} * {b}) kaysawi {mul}."))
    return out


def generate_dataset(count: int, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)

    pools = [
        build_greetings(),
        build_weather(),
        build_recipes(),
        build_travel(),
        build_shopping(),
        build_tech_support(),
        build_school(),
        build_wellness(),
        build_work(),
        build_entertainment(),
        build_sports(),
        build_definitions(),
        build_translation(),
        build_admin(),
        build_environment(),
        build_jokes(),
        build_motivation(),
        build_transport(),
        build_homework_math(),
    ]

    # de-duplicate within each pool while preserving order
    deduped_pools = []
    for pool in pools:
        seen = set()
        unique_pool = []
        for pair in pool:
            if pair not in seen:
                seen.add(pair)
                unique_pool.append(pair)
        deduped_pools.append(unique_pool)

    n_cat = len(deduped_pools)
    base = count // n_cat
    remainder = count - base * n_cat

    selected: list[tuple[str, str]] = []
    leftovers: list[tuple[str, str]] = []
    for i, pool in enumerate(deduped_pools):
        take = base + (1 if i < remainder else 0)
        take = min(take, len(pool))
        chosen = rng.sample(pool, take) if take > 0 else []
        chosen_set = set(chosen)
        selected.extend(chosen)
        leftovers.extend(p for p in pool if p not in chosen_set)

    # top up if some categories were too small to hit their quota
    rng.shuffle(leftovers)
    idx = 0
    while len(selected) < count and idx < len(leftovers):
        if leftovers[idx] not in selected:
            selected.append(leftovers[idx])
        idx += 1

    rng.shuffle(selected)
    selected = selected[:count]

    conversations = []
    for user_msg, assistant_msg in selected:
        conversations.append(
            {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": assistant_msg},
                ]
            }
        )
    return conversations


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Training (unchanged from the original script)
# ---------------------------------------------------------------------------


def validate_messages(example: dict, index: int) -> dict:
    messages = example.get("messages")
    if not isinstance(messages, list) or len(messages) < 2:
        raise ValueError(f"Ligne {index}: `messages` doit contenir au moins deux messages.")
    valid_roles = {"system", "user", "assistant"}
    for message in messages:
        if not isinstance(message, dict) or message.get("role") not in valid_roles:
            raise ValueError(f"Ligne {index}: rôle de message invalide.")
        if not isinstance(message.get("content"), str) or not message["content"].strip():
            raise ValueError(f"Ligne {index}: contenu de message vide ou invalide.")
    if not any(message["role"] == "assistant" for message in messages):
        raise ValueError(f"Ligne {index}: aucune réponse assistant.")
    return example


def run_training(args: argparse.Namespace) -> None:
    if not args.dataset.is_file():
        raise SystemExit(f"Jeu de données introuvable : {args.dataset}")

    # Imports are deliberately here: the rest of the Brainy application does not
    # need the heavy GPU-only training dependencies.
    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    if not torch.cuda.is_available():
        raise SystemExit("GPU CUDA introuvable. Ce pipeline QLoRA doit être lancé sur une machine GPU NVIDIA.")

    dataset = load_dataset("json", data_files=str(args.dataset), split="train")
    for index, example in enumerate(dataset):
        validate_messages(example, index + 1)
    if len(dataset) < 20:
        raise SystemExit("Le jeu de données doit contenir au moins 20 conversations.")

    split = dataset.train_test_split(test_size=0.05, seed=args.seed)
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=False)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    tokenizer.padding_side = "right"

    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=dtype,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=quantization,
        torch_dtype=dtype,
        device_map="auto",
    )
    model.config.use_cache = False

    lora = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )

    # SFTTrainer formats conversational `messages` using the base model's chat
    # template. Qwen2.5's template includes the role delimiters it expects.
    training = SFTConfig(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation,
        learning_rate=args.learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=25,
        save_strategy="steps",
        save_steps=25,
        save_total_limit=2,
        bf16=dtype == torch.bfloat16,
        fp16=dtype == torch.float16,
        max_seq_length=args.max_seq_length,
        packing=False,
        report_to="none",
        seed=args.seed,
    )
    trainer = SFTTrainer(
        model=model,
        args=training,
        train_dataset=split["train"],
        eval_dataset=split["test"],
        processing_class=tokenizer,
        peft_config=lora,
    )
    trainer.train()
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))
    metrics = trainer.evaluate()
    print(f"Entraînement terminé. Adaptateur sauvegardé dans : {args.output_dir}")
    print(f"Validation : {metrics}")


def main() -> None:
    args = parse_args()

    if args.generate_dataset:
        conversations = generate_dataset(args.generate_count, seed=args.seed)
        for index, example in enumerate(conversations):
            validate_messages(example, index + 1)
        write_jsonl(args.generate_output, conversations)
        print(f"{len(conversations)} conversations générées dans : {args.generate_output}")
        return

    if args.dataset is None:
        raise SystemExit("Merci de fournir --dataset, ou d'utiliser --generate-dataset pour créer un jeu de données.")

    run_training(args)


if __name__ == "__main__":
    main()
