from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, create_engine, Session, select
from datetime import date, datetime, timedelta
from pydantic import BaseModel
from collections import Counter
import openai

# ----------------- FASTAPI APP -----------------
app = FastAPI(title="FoodTracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- MODELS -----------------
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str

class FoodItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    kcal: float
    carbs_g: float
    protein_g: float
    fat_g: float
    fiber_g: float
    default_quantity: float = 1
    unit: str = "g"             
    grams_per_unit: float = 100  

class Meal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    date: date
    meal_type: str
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MealEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meal_id: int
    food_item_id: int
    quantity_g: float
    notes: Optional[str] = None

# ----------------- DATABASE -----------------
sqlite_file_name = "foodtracker.db"
engine = create_engine(f"sqlite:///{sqlite_file_name}", echo=False)
SQLModel.metadata.create_all(engine)

# ----------------- SEED FOODS -----------------

def seed_foods():
    with Session(engine) as s:
        existing_names = {f.name for f in s.exec(select(FoodItem)).all()}
        
        foods = [
            # Breakfast
            FoodItem(name="Fruit", kcal=52, carbs_g=14, protein_g=0.3, fat_g=0.2, fiber_g=2.4, default_quantity=1, unit="piece"),
            FoodItem(name="Oats", kcal=389, carbs_g=66, protein_g=17, fat_g=7, fiber_g=11, default_quantity=1, unit="cup"),
            FoodItem(name="Nuts", kcal=607, carbs_g=21, protein_g=20, fat_g=54, fiber_g=8, default_quantity=20, unit="g"),
            FoodItem(name="Poha", kcal=130, carbs_g=25, protein_g=2, fat_g=1, fiber_g=1, default_quantity=1, unit="bowl"),
            FoodItem(name="Idly", kcal=58, carbs_g=12, protein_g=2, fat_g=0.3, fiber_g=1, default_quantity=2, unit="pieces"),
            FoodItem(name="Dosa", kcal=133, carbs_g=18, protein_g=3, fat_g=5, fiber_g=1, default_quantity=1, unit="piece"),
            FoodItem(name="Rava Idly", kcal=100, carbs_g=20, protein_g=2, fat_g=0.5, fiber_g=1, default_quantity=2, unit="pieces"),
            FoodItem(name="Dalia/Upma", kcal=150, carbs_g=27, protein_g=5, fat_g=3, fiber_g=4, default_quantity=1, unit="bowl"),
            FoodItem(name="Adai", kcal=180, carbs_g=30, protein_g=6, fat_g=5, fiber_g=5, default_quantity=1, unit="piece"),
            FoodItem(name="Almond Milk", kcal=15, carbs_g=1, protein_g=0.5, fat_g=1.2, fiber_g=0, default_quantity=1, unit="glass"),

            # Lunch
            FoodItem(name="Millets", kcal=119, carbs_g=23.5, protein_g=3.5, fat_g=1, fiber_g=3, default_quantity=1, unit="cup"),
            FoodItem(name="Sambhar", kcal=110, carbs_g=18, protein_g=4, fat_g=3, fiber_g=5, default_quantity=1, unit="bowl"),
            FoodItem(name="Rasam", kcal=30, carbs_g=5, protein_g=1, fat_g=0.5, fiber_g=1, default_quantity=1, unit="bowl"),
            FoodItem(name="Subzi / Sabzi", kcal=80, carbs_g=10, protein_g=3, fat_g=4, fiber_g=5, default_quantity=1, unit="bowl"),
            FoodItem(name="Dal", kcal=120, carbs_g=20, protein_g=9, fat_g=1, fiber_g=7, default_quantity=1, unit="bowl"),
            FoodItem(name="Rice", kcal=130, carbs_g=28, protein_g=2.7, fat_g=0.3, fiber_g=0.4, default_quantity=1, unit="cup"),
            FoodItem(name="Chapati / Roti", kcal=70, carbs_g=15, protein_g=3, fat_g=1, fiber_g=2, default_quantity=2, unit="pieces"),
            FoodItem(name="Khichdi", kcal=150, carbs_g=28, protein_g=5, fat_g=3, fiber_g=5, default_quantity=1, unit="bowl"),
            FoodItem(name="Avial / Mixed Veg", kcal=90, carbs_g=10, protein_g=3, fat_g=5, fiber_g=6, default_quantity=1, unit="bowl"),

            # Snacks
            FoodItem(name="Roasted Chana", kcal=350, carbs_g=60, protein_g=20, fat_g=6, fiber_g=15, default_quantity=1, unit="cup"),
            FoodItem(name="Banana", kcal=89, carbs_g=23, protein_g=1, fat_g=0.3, fiber_g=2.6, default_quantity=1, unit="piece"),
            FoodItem(name="Kiwi", kcal=61, carbs_g=15, protein_g=1, fat_g=0.5, fiber_g=3, default_quantity=1, unit="piece"),
            FoodItem(name="Nuts Overload", kcal=600, carbs_g=20, protein_g=15, fat_g=50, fiber_g=7, default_quantity=30, unit="g"),
            FoodItem(name="Gado Gado", kcal=220, carbs_g=18, protein_g=10, fat_g=12, fiber_g=5, default_quantity=1, unit="bowl"),

            # Dinner
            FoodItem(name="Soy Chunks", kcal=345, carbs_g=33, protein_g=52, fat_g=1.2, fiber_g=10, default_quantity=50, unit="g"),
            FoodItem(name="Tofu Curry", kcal=150, carbs_g=5, protein_g=10, fat_g=10, fiber_g=2, default_quantity=1, unit="bowl"),
            FoodItem(name="Grilled Veggies", kcal=50, carbs_g=10, protein_g=2, fat_g=1, fiber_g=3, default_quantity=1, unit="bowl"),
            FoodItem(name="Cashew Paste", kcal=550, carbs_g=30, protein_g=18, fat_g=45, fiber_g=3, default_quantity=1, unit="tbsp"),
            FoodItem(name="Sprouts Salad", kcal=80, carbs_g=12, protein_g=5, fat_g=2, fiber_g=6, default_quantity=1, unit="bowl"),
            FoodItem(name="Millet Khichdi", kcal=160, carbs_g=28, protein_g=5, fat_g=3, fiber_g=5, default_quantity=1, unit="bowl"),
            FoodItem(name="Soup / Light Veg", kcal=40, carbs_g=5, protein_g=2, fat_g=1, fiber_g=2, default_quantity=1, unit="bowl"),
        ]
        
        new_foods = [f for f in foods if f.name not in existing_names]
        s.add_all(new_foods)
        s.commit()
        print(f"✅ Seeded {len(new_foods)} new foods.")


seed_foods()

# ----------------- SCHEMAS -----------------
class MealEntryCreate(BaseModel):
    food_item_id: int
    quantity_g: float
    notes: Optional[str] = None

class MealCreate(BaseModel):
    user_id: int
    date: date
    meal_type: str
    name: Optional[str] = None
    entries: List[MealEntryCreate] = []

class NewFoodItem(BaseModel):
    name: str
    unit: str = "g"
    standard_quantity: float = 100  

# ----------------- HELPER -----------------
def compute_meal_nutrients(meal_id: int, session: Session):
    entries = session.exec(select(MealEntry).where(MealEntry.meal_id==meal_id)).all()
    totals = {"kcal": 0, "carbs_g": 0, "protein_g": 0, "fat_g": 0, "fiber_g": 0}
    for e in entries:
        food = session.get(FoodItem, e.food_item_id)
        if not food: continue
        factor = e.quantity_g / food.grams_per_unit
        totals["kcal"] += food.kcal * factor
        totals["carbs_g"] += food.carbs_g * factor
        totals["protein_g"] += food.protein_g * factor
        totals["fat_g"] += food.fat_g * factor
        totals["fiber_g"] += food.fiber_g * factor
    for k in totals: totals[k] = round(totals[k], 2)
    return totals

def get_nutrients_from_llm(food_name: str, quantity: float, unit: str):
    return {"kcal": 60, "carbs_g": 15, "protein_g": 1, "fat_g": 0.5, "fiber_g": 2}
    # os.environ["OPENAI_API_KEY"] = "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"
    # """
    # Call a LLM to get the nutrients per 'quantity unit' of the food.
    # Returns a dict: {"kcal": ..., "carbs_g": ..., "protein_g": ..., "fat_g": ..., "fiber_g": ...}
    # Uses gpt-3.5-turbo which is free-tier compatible.
    # """
    # prompt = f"""
    # Provide the nutrition information for {quantity} {unit} of {food_name}.
    # Format your response as JSON with keys: kcal, carbs_g, protein_g, fat_g, fiber_g.
    # """

    # try:
    #     response = openai.ChatCompletion.create(
    #         model="gpt-3.5-turbo",
    #         messages=[{"role": "user", "content": prompt}],
    #         temperature=0
    #     )
    #     # extract JSON content safely
    #     content = response.choices[0].message["content"]
    #     import json
    #     nutrients = json.loads(content)
    #     # ensure all keys exist
    #     for k in ["kcal", "carbs_g", "protein_g", "fat_g", "fiber_g"]:
    #         nutrients[k] = float(nutrients.get(k, 0))
    #     return nutrients
    # except Exception as e:
    #     print("Error fetching nutrients from LLM:", e)
    #     return None


# ----------------- ENDPOINTS -----------------
@app.post("/users/")
def create_user(user: User):
    with Session(engine) as s:
        s.add(user)
        s.commit()
        s.refresh(user)
        return user

@app.get("/foods/")
def list_foods():
    with Session(engine) as s:
        return s.exec(select(FoodItem)).all()

@app.post("/foods/new")
def add_new_food(food_in: NewFoodItem):
    nutrient_info = get_nutrients_from_llm(food_in.name, food_in.standard_quantity, food_in.unit)
    if not nutrient_info:
        return {"error": "Could not fetch nutrient info from LLM."}
    new_food = FoodItem(
        name=food_in.name,
        unit=food_in.unit,
        grams_per_unit=food_in.standard_quantity,
        kcal=nutrient_info["kcal"],
        carbs_g=nutrient_info["carbs_g"],
        protein_g=nutrient_info["protein_g"],
        fat_g=nutrient_info["fat_g"],
        fiber_g=nutrient_info["fiber_g"],
    )
    with Session(engine) as s:
        s.add(new_food)
        s.commit()
        s.refresh(new_food)
        return new_food

@app.post("/meals/")
def create_meal(meal_in: MealCreate):
    with Session(engine) as s:
        existing_meal = s.exec(
            select(Meal).where(
                Meal.user_id == meal_in.user_id,
                Meal.meal_type == meal_in.meal_type,
                Meal.date == meal_in.date
            )
        ).first()
        meal = existing_meal or Meal(
            user_id=meal_in.user_id,
            date=meal_in.date,
            meal_type=meal_in.meal_type,
            name=meal_in.name
        )
        if not existing_meal:
            s.add(meal)
            s.commit()
            s.refresh(meal)
        for e in meal_in.entries:
            me = MealEntry(
                meal_id=meal.id,
                food_item_id=e.food_item_id,
                quantity_g=e.quantity_g,
                notes=e.notes
            )
            s.add(me)
        s.commit()
        totals = compute_meal_nutrients(meal.id, s)
        return {"meal_id": meal.id, "totals": totals}

@app.get("/meals/{user_id}/{date_str}")
def get_meals(user_id: int, date_str: str):
    d = date.fromisoformat(date_str)
    with Session(engine) as s:
        meals = s.exec(select(Meal).where(Meal.user_id==user_id, Meal.date==d)).all()
        result = []
        for m in meals:
            entries = s.exec(select(MealEntry).where(MealEntry.meal_id==m.id)).all()
            totals = compute_meal_nutrients(m.id, s)
            result.append({"meal": m, "entries": entries, "totals": totals})
        return result

@app.get("/recent-meals/{user_id}/{meal_type}")
def recent_meals(user_id: int, meal_type: str, days: int = 30, top_n: int = 5):
    cutoff_date = date.today() - timedelta(days=days)
    with Session(engine) as s:
        meals = s.exec(
            select(Meal).where(
                Meal.user_id == user_id,
                Meal.meal_type == meal_type.lower(),
                Meal.date >= cutoff_date
            )
        ).all()
        food_counter = Counter()
        for m in meals:
            entries = s.exec(select(MealEntry).where(MealEntry.meal_id == m.id)).all()
            for e in entries:
                food_counter[e.food_item_id] += 1
        top_food_ids = [fid for fid, _ in food_counter.most_common(top_n)]
        all_foods = s.exec(select(FoodItem)).all()
        top_foods = [f for f in all_foods if f.id in top_food_ids]
        remaining_foods = [f for f in all_foods if f.id not in top_food_ids]
        top_foods.sort(key=lambda f: top_food_ids.index(f.id))
        result = [{"id": f.id, "name": f.name} for f in top_foods + remaining_foods]
        return result

@app.get("/daily-summary/{user_id}/{date_str}")
def daily_summary(user_id: int, date_str: str):
    d = date.fromisoformat(date_str)
    with Session(engine) as s:
        meals = s.exec(select(Meal).where(Meal.user_id==user_id, Meal.date==d)).all()
        totals = {"kcal": 0, "carbs_g": 0, "protein_g": 0, "fat_g": 0, "fiber_g": 0}
        for m in meals:
            meal_totals = compute_meal_nutrients(m.id, s)
            for k in totals: totals[k] += meal_totals[k]
        for k in totals: totals[k] = round(totals[k], 2)
        nudges = []
        if totals["kcal"] < 1200:
            nudges.append("You need more calories today!")
        elif totals["kcal"] > 2500:
            nudges.append("Try to eat a little less today.")
        else:
            nudges.append("Great! Your calorie intake is balanced.")
        return {"date": d, "totals": totals, "nudges": nudges}

@app.get("/monthly-summary/{user_id}/{year}/{month}")
def monthly_summary(user_id: int, year: int, month: int):
    from calendar import monthrange
    days_in_month = monthrange(year, month)[1]
    summary = []

    with Session(engine) as s:
        for day in range(1, days_in_month + 1):
            d = date(year, month, day)
            meals = s.exec(select(Meal).where(Meal.user_id == user_id, Meal.date == d)).all()
            totals = {"kcal": 0, "carbs_g": 0, "protein_g": 0, "fat_g": 0, "fiber_g": 0}

            for m in meals:
                meal_totals = compute_meal_nutrients(m.id, s)
                for k in totals:
                    totals[k] += meal_totals[k]

            for k in totals:
                totals[k] = round(totals[k], 2)

            summary.append({"date": d.isoformat(), "totals": totals})

    return summary







