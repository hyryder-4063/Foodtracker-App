# frontend_app.py
import streamlit as st
import requests
import pandas as pd
from collections import Counter


# st.cache_data.clear()

# ---------- CONFIG ----------
BACKEND_URL = "http://127.0.0.1:8000"
USER_ID = 1
TOP_N = 5
RECENT_LIMIT = 30

st.set_page_config(page_title="Food Tracker", layout="wide")
st.title("🍽️ Food Tracker Dashboard")

# ---------- SIDEBAR INPUT ----------
st.sidebar.header("Enter Details")
selected_date = st.sidebar.date_input("Select Date")
meal_type = st.sidebar.selectbox("Meal Type", ["Breakfast", "Lunch", "Snack", "Dinner"])

# ---------- FETCHERS ----------
@st.cache_data(show_spinner=False)
def fetch_all_foods():
    try:
        res = requests.get(f"{BACKEND_URL}/foods/", timeout=8)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Error fetching all foods: {e}")
    return []

@st.cache_data(show_spinner=False)
def fetch_recent_meals(user_id: int, meal_type_str: str, limit: int = RECENT_LIMIT):
    try:
        url = f"{BACKEND_URL}/recent-meals/{user_id}/{meal_type_str}"
        res = requests.get(url, timeout=8)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Error fetching recent meals: {e}")
    return []

@st.cache_data(show_spinner=False)
def fetch_existing_meal(user_id: int, date_str: str):
    try:
        res = requests.get(f"{BACKEND_URL}/meals/{user_id}/{date_str}", timeout=8)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Error fetching existing meals: {e}")
    return []



# ---------- PREPARE FOOD LISTS ----------
all_foods = fetch_all_foods()
if not all_foods:
    st.warning("No foods returned from backend. Confirm backend is running and /foods/ works.")

food_by_id = {f['id']: f for f in all_foods}
food_name_by_id = {f['id']: f['name'] for f in all_foods}
food_id_by_name = {f['name']: f['id'] for f in all_foods}
all_names_sorted = sorted([f['name'] for f in all_foods])

recent_meals = fetch_recent_meals(USER_ID, meal_type.lower(), RECENT_LIMIT)

recent_food_ids = []
if isinstance(recent_meals, list):
    for m in recent_meals:
        if isinstance(m, dict) and 'id' in m and 'name' in m:
            recent_food_ids.append(m['id'])
            continue
        if isinstance(m, dict) and 'entries' in m and isinstance(m['entries'], list):
            for e in m['entries']:
                if isinstance(e, dict):
                    if 'food_item_id' in e:
                        recent_food_ids.append(e['food_item_id'])
                    elif 'food_item' in e and isinstance(e['food_item'], dict) and 'id' in e['food_item']:
                        recent_food_ids.append(e['food_item']['id'])
                    elif 'id' in e and isinstance(e['id'], int):
                        recent_food_ids.append(e['id'])
        elif isinstance(m, dict) and 'food_item_id' in m:
            recent_food_ids.append(m['food_item_id'])

counter = Counter(recent_food_ids)
most_common_ids = [fid for fid, _ in counter.most_common(TOP_N)]
most_common_names = [food_name_by_id.get(fid) for fid in most_common_ids if fid in food_name_by_id]
seen = set()
most_common_names = [n for n in most_common_names if n and (n not in seen and not seen.add(n))]
other_names = [n for n in all_names_sorted if n not in most_common_names]

# ---------- DROPDOWN WITH "ADD NEW FOOD" ----------
food_options = most_common_names + ["+ Add New Food"] + other_names
selected_food = st.sidebar.selectbox("Select Food", food_options)

# ---------- DYNAMIC NEW FOOD INPUT ----------
new_food_id = None
if selected_food == "+ Add New Food":
    new_food_name = st.sidebar.text_input("Food Name")
    new_food_unit = st.sidebar.selectbox("Unit", ["g", "ml", "piece", "cup"])
    new_food_qty = st.sidebar.number_input("Standard Quantity", value=100, min_value=1)
    if st.sidebar.button("Add Food"):
        try:
            res = requests.post(
                f"{BACKEND_URL}/foods/new",
                json={"name": new_food_name, "unit": new_food_unit, "standard_quantity": new_food_qty},
                timeout=8
            )
            data = res.json()
            if res.status_code in (200, 201) and "id" in data:
                st.success(f"Food '{new_food_name}' added!")
                fetch_all_foods.clear()
                all_foods = fetch_all_foods()
                food_by_id = {f['id']: f for f in all_foods}
                food_name_by_id = {f['id']: f['name'] for f in all_foods}
                food_id_by_name = {f['name']: f['id'] for f in all_foods}
                selected_food = new_food_name
                new_food_id = data["id"]
            else:
                st.error(f"Failed to add food: {data.get('error', res.text)}")
        except Exception as e:
            st.error(f"Error adding food: {e}")

selected_food_id = new_food_id or food_id_by_name.get(selected_food)

# ---------- QUANTITY INPUT ----------
food_obj = food_by_id.get(selected_food_id, {})
unit = food_obj.get("unit", "g")
default_qty = food_obj.get("default_quantity", 100)

# Decide if we want int or float input
if unit in ["piece", "cup", "bowl", "glass", "tbsp", "pieces"]:
    default_qty = int(default_qty)
    step = 1
else:
    default_qty = float(default_qty)
    step = 10

quantity = st.sidebar.number_input(
    f"Quantity ({unit})",
    value=default_qty,
    min_value=0,
    step=step
)




notes = st.sidebar.text_area("Notes (optional)")

# ---------- EXISTING MEAL ----------
existing_meals = fetch_existing_meal(USER_ID, str(selected_date))
meal_for_type = None
for m in existing_meals:
    if m.get("meal") and m["meal"]["meal_type"] == meal_type.lower():
        meal_for_type = m
        break

if meal_for_type:
    st.sidebar.subheader("Existing Entries")
    for e in meal_for_type.get("entries", []):
        food_id = e.get("food_item_id")
        food_name_disp = food_name_by_id.get(food_id, "Unknown")
        # Get the correct unit and default quantity from food_by_id
        food_info = food_by_id.get(food_id, {})
        unit = food_info.get("unit", "g")
        qty = e.get("quantity_g", food_info.get("standard_quantity", 100))
        st.sidebar.write(f"{food_name_disp} - {qty} {unit}")


# ---------- SUBMIT MEAL ----------
if st.sidebar.button("Submit Meal"):
    if selected_food_id is None:
        st.error("Selected food not found.")
    else:
        new_entry = {
            "food_item_id": selected_food_id,
            "quantity_g": quantity,
            "notes": notes
        }
        meal_data = {
            "user_id": USER_ID,
            "date": str(selected_date),
            "meal_type": meal_type.lower(),
            "entries": [new_entry]
        }
        try:
            res = requests.post(f"{BACKEND_URL}/meals/", json=meal_data, timeout=8)
            if res.status_code in (200, 201):
                st.success("Meal logged successfully!")
                fetch_recent_meals.clear()
                fetch_existing_meal.clear()
            else:
                st.error(f"Failed to submit meal: {res.status_code} - {res.text}")
        except Exception as e:
            st.error(f"Error submitting meal: {e}")

# ---------- DAILY SUMMARY ----------
if st.button("Show Daily Summary"):
    try:
        res = requests.get(f"{BACKEND_URL}/daily-summary/{USER_ID}/{selected_date}", timeout=8)
        if res.status_code == 200:
            summary = res.json()
            st.subheader(f"Summary for {selected_date}")
            st.write(summary.get("totals", {}))
            nudges = summary.get("nudges", [])
            if nudges:
                st.info(nudges[0])
        else:
            st.error(f"Failed to fetch daily summary: {res.status_code} - {res.text}")
    except Exception as e:
        st.error(f"Error fetching daily summary: {e}")

# ---------- MONTHLY SUMMARY ----------
if st.button("Show Monthly Summary"):
    try:
        res = requests.get(f"{BACKEND_URL}/monthly-summary/{USER_ID}/{selected_date.year}/{selected_date.month}", timeout=10)
        if res.status_code == 200:
            data = pd.DataFrame(res.json())
            if "totals" not in data.columns:
                data["totals"] = [{"kcal": 0}] * len(data)
            data["kcal"] = data["totals"].apply(lambda x: x.get("kcal", 0) if isinstance(x, dict) else 0)
            data = data.set_index("date")
            st.line_chart(data["kcal"])
        else:
            st.error(f"Failed to fetch monthly summary: {res.status_code} - {res.text}")
    except Exception as e:
        st.error(f"Error fetching monthly summary: {e}")


# # frontend_app.py
# import streamlit as st
# import requests
# import pandas as pd
# from collections import Counter

# # ---------- CONFIG ----------
# BACKEND_URL = "http://127.0.0.1:8000"   # replace with your ngrok/localtunnel URL if needed
# USER_ID = 1
# TOP_N = 5           # how many top items to surface
# RECENT_LIMIT = 30   # how many recent meals to consider (backend may return fewer)

# st.set_page_config(page_title="Food Tracker", layout="wide")
# st.title("🍽️ Food Tracker Dashboard")

# # ---------- SIDEBAR INPUT ----------
# st.sidebar.header("Enter Details")
# selected_date = st.sidebar.date_input("Select Date")
# meal_type = st.sidebar.selectbox("Meal Type", ["Breakfast", "Lunch", "Snack", "Dinner"])

# # ---------- FETCHERS ----------
# @st.cache_data(show_spinner=False)
# def fetch_all_foods():
#     try:
#         res = requests.get(f"{BACKEND_URL}/foods/", timeout=8)
#         if res.status_code == 200:
#             return res.json()
#     except Exception as e:
#         st.error(f"Error fetching all foods: {e}")
#     return []

# @st.cache_data(show_spinner=False)
# def fetch_recent_meals(user_id: int, meal_type_str: str, limit: int = RECENT_LIMIT):
#     """
#     Calls /recent-meals/{user_id}/{meal_type}. The backend may return a list of recent meals,
#     each possibly containing an 'entries' list. This function will return that raw list (or []).
#     """
#     try:
#         # If your backend supports a query param for limit you can append it; otherwise backend may ignore it.
#         url = f"{BACKEND_URL}/recent-meals/{user_id}/{meal_type_str}"
#         res = requests.get(url, timeout=8)
#         if res.status_code == 200:
#             return res.json()
#     except Exception as e:
#         st.error(f"Error fetching recent meals: {e}")
#     return []

# # ---------- PREPARE FOOD LISTS ----------
# all_foods = fetch_all_foods()
# if not all_foods:
#     st.warning("No foods returned from backend. Confirm backend is running and /foods/ works.")
# # id -> food dict & name -> id maps
# food_by_id = {f['id']: f for f in all_foods}
# food_name_by_id = {f['id']: f['name'] for f in all_foods}
# food_id_by_name = {f['name']: f['id'] for f in all_foods}
# all_names_sorted = sorted([f['name'] for f in all_foods])

# # Get recent meals and compute counts of food_item_id for the given meal type
# recent_meals = fetch_recent_meals(USER_ID, meal_type.lower(), RECENT_LIMIT)

# # Normalize recent_meals format to a list of entries we can parse.
# # Backend may return a list of meals where each meal has 'entries' (list of {food_item_id,...}),
# # or may return a list of food objects — handle both.
# recent_food_ids = []
# if isinstance(recent_meals, list):
#     for m in recent_meals:
#         # If item is a full food object (e.g., {'id': 5, 'name': 'Oats', ...})
       
#         if isinstance(m, dict) and 'id' in m and 'name' in m:
#             recent_food_ids.append(m['id'])

       
#             continue

#         # If item is a meal object with 'entries'
#         if isinstance(m, dict) and 'entries' in m and isinstance(m['entries'], list):
#             for e in m['entries']:
#                 # entry could be dict with 'food_item_id' or 'food_item' etc.
#                 if isinstance(e, dict):
#                     if 'food_item_id' in e:
#                         recent_food_ids.append(e['food_item_id'])
#                     elif 'food_item' in e and isinstance(e['food_item'], dict) and 'id' in e['food_item']:
#                         recent_food_ids.append(e['food_item']['id'])
#                     # fallback: maybe entry directly stores id
#                     elif 'id' in e and isinstance(e['id'], int):
#                         recent_food_ids.append(e['id'])
#         # If m itself is a food-entry-like dict with 'food_item_id'
#         elif isinstance(m, dict) and 'food_item_id' in m:
#             recent_food_ids.append(m['food_item_id'])
#         # Else ignore unknown shape
# else:
#     # not a list — ignore
#     recent_food_ids = []

# # Count frequencies and pick top N
# counter = Counter(recent_food_ids)
# most_common_ids = [fid for fid, _ in counter.most_common(TOP_N)]

# # Map ids -> names and filter out unknown ids (that aren't in food_by_id)
# most_common_names = [food_name_by_id.get(fid) for fid in most_common_ids if fid in food_name_by_id]
# # Remove None and duplicates preserving order
# seen = set()
# most_common_names = [n for n in most_common_names if n and (n not in seen and not seen.add(n))]

# # Now build the dropdown ordering: top recent names first, then remaining all foods sorted
# other_names = [n for n in all_names_sorted if n not in most_common_names]
# dropdown_order = most_common_names + other_names

# # ---------- SIDEBAR - FOOD SELECTION ----------
# selected_food = st.sidebar.selectbox("Select Food", dropdown_order)
# # default quantity: try to provide a heuristic default from the food item if present (not all foods have defaults)
# default_qty = 100  # fallback grams
# selected_food_id = food_id_by_name.get(selected_food)
# if selected_food_id:
#     # if backend's food item contains some hint (not in your current model), you could extract it here
#     pass

# quantity = st.sidebar.number_input("Quantity (grams)", value=default_qty, min_value=0, step=10)
# notes = st.sidebar.text_area("Notes (optional)")

# # ---------- FETCH EXISTING MEAL FOR SELECTED DATE & TYPE ----------
# @st.cache_data(show_spinner=False)
# def fetch_existing_meal(user_id: int, date_str: str):
#     try:
#         res = requests.get(f"{BACKEND_URL}/meals/{user_id}/{date_str}", timeout=8)
#         if res.status_code == 200:
#             return res.json()  # returns list of meals with 'entries'
#     except Exception as e:
#         st.error(f"Error fetching existing meals: {e}")
#     return []

# existing_meals = fetch_existing_meal(USER_ID, str(selected_date))
# meal_for_type = None
# for m in existing_meals:
#     if m.get("meal") and m["meal"]["meal_type"] == meal_type.lower():
#         meal_for_type = m
#         break

# # Display existing entries if any
# if meal_for_type:
#     st.sidebar.subheader("Existing Entries")
#     for e in meal_for_type.get("entries", []):
#         food_name = food_name_by_id.get(e["food_item_id"], "Unknown")
#         st.sidebar.write(f"{food_name} - {e.get('quantity_g', 0)} g")


# # ---------- SUBMIT MEAL ----------
# if st.sidebar.button("Submit Meal"):
#     if selected_food_id is None:
#         st.error("Selected food not found in foods list (backend mismatch).")
#     else:
#         new_entry = {
#             "food_item_id": selected_food_id,
#             "quantity_g": quantity,
#             "notes": notes
#         }
#         if meal_for_type:
#             # Append to existing meal by sending entries to same meal_id
#             meal_id = meal_for_type["meal"]["id"]
#             meal_data = {
#                 "user_id": USER_ID,
#                 "date": str(selected_date),
#                 "meal_type": meal_type.lower(),
#                 "entries": [new_entry]
#             }
#         else:
#             # Create new meal
#             meal_data = {
#                 "user_id": USER_ID,
#                 "date": str(selected_date),
#                 "meal_type": meal_type.lower(),
#                 "entries": [new_entry]
#             }

#         try:
#             res = requests.post(f"{BACKEND_URL}/meals/", json=meal_data, timeout=8)
#             if res.status_code in (200, 201):
#                 st.success("Meal logged successfully!")
#                 fetch_recent_meals.clear()
#                 fetch_existing_meal.clear()
#             else:
#                 st.error(f"Failed to submit meal: {res.status_code} - {res.text}")
#         except Exception as e:
#             st.error(f"Error submitting meal: {e}")


# # ---------- DAILY SUMMARY ----------
# if st.button("Show Daily Summary"):
#     try:
#         res = requests.get(f"{BACKEND_URL}/daily-summary/{USER_ID}/{selected_date}", timeout=8)
#         if res.status_code == 200:
#             summary = res.json()
#             st.subheader(f"Summary for {selected_date}")
#             st.write(summary.get("totals", {}))
#             nudges = summary.get("nudges", [])
#             if nudges:
#                 st.info(nudges[0])
#         else:
#             st.error(f"Failed to fetch daily summary: {res.status_code} - {res.text}")
#     except Exception as e:
#         st.error(f"Error fetching daily summary: {e}")

# # ---------- MONTHLY SUMMARY ----------
# if st.button("Show Monthly Summary"):
#     try:
#         res = requests.get(f"{BACKEND_URL}/monthly-summary/{USER_ID}/{selected_date.year}/{selected_date.month}", timeout=10)
#         if res.status_code == 200:
#             data = pd.DataFrame(res.json())
#             # Safe handling for totals
#             if "totals" not in data.columns:
#                 data["totals"] = [{"kcal": 0}] * len(data)
#             data["kcal"] = data["totals"].apply(lambda x: x.get("kcal", 0) if isinstance(x, dict) else 0)
#             data = data.set_index("date")
#             st.line_chart(data["kcal"])
#         else:
#             st.error(f"Failed to fetch monthly summary: {res.status_code} - {res.text}")
#     except Exception as e:
#         st.error(f"Error fetching monthly summary: {e}")
