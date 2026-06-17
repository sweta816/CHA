from typing import List
import json
from openCHA.tasks import BaseTask

# ─── Load nutrient database once at startup ─────────────────────────
def _load_nutrient_db():
    try:
        with open("./data/food_nutrient_database.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"foods": []}


_nutrient_data = _load_nutrient_db()


class NutritionInfo(BaseTask):

    name: str = "nutrition_info"
    chat_name: str = "NutritionInfo"
    description: str = (
        "Looks up EXACT nutrient values (calories, protein, carbohydrates, "
        "fat, iron, calcium) for a SPECIFIC named food item such as rice, "
        "roti, egg, milk, dal, sattu, makhana, banana, ragi, or vegetables. "
        "ALWAYS use this task for number-based questions like 'how much "
        "protein in rice', 'calories in egg', 'iron content of dal', or "
        "'nutrition value of sattu'. "
        "Do NOT use this for general diet advice, symptoms, or meal "
        "suggestions — use nutrition_search for those instead."
    )
    dependencies: List = []
    inputs: List = [
        "The name of a single food item to look up, e.g. 'rice', 'roti', "
        "'egg', 'sattu', 'makhana', 'moong dal'."
    ]
    outputs: List = [
        "Exact nutrient values (calories, protein, carbohydrates, fat, "
        "iron, calcium) for the requested food, per common serving."
    ]
    output_type: bool = False

    def _find_food(self, query: str):
        query = query.lower().strip()
        foods = _nutrient_data.get("foods", [])

        # Exact name match first
        for food in foods:
            if food["name"].lower() == query:
                return food

        # Alias exact match
        for food in foods:
            for alias in food.get("aliases", []):
                if query == alias.lower():
                    return food

        # Partial / contains match (fallback)
        for food in foods:
            if query in food["name"].lower() or food["name"].lower() in query:
                return food
            for alias in food.get("aliases", []):
                if query in alias.lower() or alias.lower() in query:
                    return food

        return None

    def _execute(self, inputs: List) -> str:
        query = inputs[0]
        food = self._find_food(query)

        if food is None:
            return (
                f"No exact nutrient data found for '{query}' in the "
                f"database. Available foods include: rice, roti, dal "
                f"(chana/arhar/moong/masoor), egg, milk, curd, sattu, "
                f"makhana, banana, peanuts, potato, spinach, ragi, bajra, "
                f"jowar, jaggery. Try one of these or use nutrition_search "
                f"for general advice instead."
            )

        return (
            f"{food['name'].title()} (per {food['serving']}): "
            f"{food['calories']} kcal, "
            f"{food['protein_g']}g protein, "
            f"{food['carbs_g']}g carbohydrates, "
            f"{food['fat_g']}g fat, "
            f"{food['iron_mg']}mg iron, "
            f"{food['calcium_mg']}mg calcium."
        )
