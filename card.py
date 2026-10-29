from dataclasses import dataclass

@dataclass
class Card:
    id: int
    pair_id: str
    image_path: str
    description: str = ""
    display_pair_id: str = ""
    pair_color: str = "#70829d"

    open: bool = False
    matched: bool = False

    def to_dict(self):
        return {
            "id": self.id,
            "pair_id": self.pair_id,
            "display_pair_id": self.display_pair_id or self.pair_id,
            "image_path": self.image_path,
            "description": self.description,
            "pair_color": self.pair_color,
            "open": self.open,
            "matched": self.matched,
        }