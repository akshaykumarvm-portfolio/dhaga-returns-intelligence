"""Generate synthetic, real-shaped data for the returns & review
intelligence MVP.

Mirrors the shape described in the Dhaga & Co. brief: Hinglish mixed with
English, typos, the "Other" free-text box, product reviews, and support
tickets. Every row carries a hidden `true_category` field for measuring
classifier/evaluator accuracy later — strip this column before it ever
reaches a prompt.

Usage:
    python scripts/generate_synthetic_data.py
    python scripts/generate_synthetic_data.py --n-returns 1000 --n-tickets 1000 --n-reviews 1000
"""
from __future__ import annotations

import argparse
import csv
import random
import uuid
from pathlib import Path

random.seed(42)


def order_id() -> str:
    return uuid.uuid4().hex[:8]

CATEGORIES = [
    "fit",
    "fabric_quality",
    "wrong_item",
    "changed_mind",
    "delivery_damage",
    "other",
]

SKU_PREFIXES = ["WMN", "KID", "MEN"]

# --- Free-text templates per (source, category) ------------------------
# {size} / {color} / {other_color} get filled in. Hinglish and typos are
# intentional — this is what "real-shaped input" means in the brief.

RETURN_TEMPLATES = {
    "fit": [
        "size chart galat tha, {size} order kiya but bahut tight aaya",
        "runs small, ordered my usual {size} but it doesn't fit at all",
        "kandhe se tight hai, return kar rahi hu",
        "too loose around the waist, need one size down",
        "fitting sahi nahi hai, length bhi short hai",
    ],
    "fabric_quality": [
        "fabric bahut thin hai, first wash mein hi fade ho gaya",
        "stitching came apart after one wear",
        "material feels cheap, not like the photos",
        "color ekdum different tha jo dikha tha usse",
        "quality bahut kharab, paisa waste",
    ],
    "wrong_item": [
        "ordered {color} kurti mila {other_color} bheja",
        "wrong size delivered, ordered L got S",
        "different product bhej diya, ye to kuch aur hai",
        "received a men's item instead of kidswear",
    ],
    "changed_mind": [
        "no longer needed, changed my mind",
        "found a better option elsewhere",
        "ordered by mistake, cancel kardo",
        "not required anymore",
    ],
    "delivery_damage": [
        "packet phata hua aaya, item torn hai",
        "box was crushed, product damaged inside",
        "stains on the fabric on arrival",
        "zip broken jab khola tab",
    ],
    "other": [
        "just didn't like it",
        "not as expected",
        "return kar rahi hu, bas pasand nahi aaya",
        "meh, thik nahi laga",
        "expected better tbh",
    ],
}

TICKET_TEMPLATES = {
    "delivery_damage": [
        "mera order damaged aaya hai, refund chahiye",
        "the package arrived broken, please assist",
    ],
    "wrong_item": [
        "wrong item bheja hai apne, kab tak sahi wala aayega",
        "received incorrect product, need exchange asap",
    ],
    "fit": [
        "size guide follow kiya phir bhi galat size aaya",
        "the sizing is way off from what's on the app",
    ],
    "other": [
        "kaha hai mera order? 5 din ho gaye",
        "where is my order, tracking not updating",
        "kab tak deliver hoga bataiye please",
        "refund abhi tak nahi aaya, 10 din ho gaye",
        "app crash ho raha hai baar baar",
    ],
    "changed_mind": [
        "cancel this order please, don't need it anymore",
    ],
    "fabric_quality": [
        "product quality bahut kharab hai, complain karna hai",
    ],
}

REVIEW_TEMPLATES = {
    "fit": [
        ("2", "chota nikla, size up lena chahiye tha"),
        ("3", "runs slightly small, order one size up"),
    ],
    "fabric_quality": [
        ("1", "fabric bahut kharab, do wash mein hi kharab ho gaya"),
        ("2", "not worth the price, quality average hai"),
    ],
    "wrong_item": [
        ("1", "got a completely different design than ordered"),
    ],
    "changed_mind": [
        ("3", "okay product but not what I expected style-wise"),
    ],
    "delivery_damage": [
        ("1", "arrived with a tear, disappointed"),
    ],
    "other": [
        ("5", "loved it, perfect for the mehndi function"),
        ("4", "good quality for the price, will order again"),
        ("5", "office wear ke liye perfect"),
        ("3", "decent, nothing special"),
    ],
}

TYPO_SWAPS = [
    ("hai", "h"),
    ("bahut", "bhut"),
    ("please", "pls"),
    ("received", "recieved"),
]


def add_noise(text: str) -> str:
    """Randomly apply one typo swap to mimic real free text."""
    if random.random() < 0.3:
        old, new = random.choice(TYPO_SWAPS)
        text = text.replace(old, new)
    return text


def random_sku() -> str:
    return f"{random.choice(SKU_PREFIXES)}-{random.randint(1000, 9999)}"


def gen_returns(n: int) -> list[dict]:
    rows = []
    for i in range(n):
        cat = random.choice(CATEGORIES)
        template = random.choice(RETURN_TEMPLATES[cat])
        text = template.format(
            size=random.choice(["S", "M", "L", "XL"]),
            color=random.choice(["red", "blue", "black", "beige"]),
            other_color=random.choice(["green", "white", "maroon"]),
        )
        rows.append(
            {
                "return_id": f"RET{i:05d}",
                "order_id": order_id(),
                "sku": random_sku(),
                "dropdown_reason": "Other",
                "free_text": add_noise(text),
                "true_category": cat,  # hidden ground truth — do not feed to model
            }
        )
    return rows


def gen_tickets(n: int) -> list[dict]:
    rows = []
    for i in range(n):
        cat = random.choice(list(TICKET_TEMPLATES))
        text = random.choice(TICKET_TEMPLATES[cat])
        rows.append(
            {
                "ticket_id": f"TCK{i:05d}",
                "order_id": order_id(),
                "message": add_noise(text),
                "true_category": cat,
            }
        )
    return rows


def gen_reviews(n: int) -> list[dict]:
    rows = []
    for i in range(n):
        cat = random.choice(list(REVIEW_TEMPLATES))
        rating, text = random.choice(REVIEW_TEMPLATES[cat])
        rows.append(
            {
                "review_id": f"REV{i:05d}",
                "sku": random_sku(),
                "rating": rating,
                "review_text": add_noise(text),
                "true_category": cat,
            }
        )
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-returns", type=int, default=500)
    parser.add_argument("--n-tickets", type=int, default=500)
    parser.add_argument("--n-reviews", type=int, default=500)
    parser.add_argument("--out-dir", type=Path, default=Path("data"))
    args = parser.parse_args()

    write_csv(gen_returns(args.n_returns), args.out_dir / "synthetic_returns.csv")
    write_csv(gen_tickets(args.n_tickets), args.out_dir / "synthetic_tickets.csv")
    write_csv(gen_reviews(args.n_reviews), args.out_dir / "synthetic_reviews.csv")


if __name__ == "__main__":
    main()
