from client import Strategy, Client
import random
from datetime import datetime
#from utilities.utils import write_file
import os
# times 900 pc
import random
from datetime import datetime


import random

class SmartHydroStrategy:
    def __init__(self):
        self.player_id = None
        self.initial_state = None
        self.current_state = None
        self.reservoir_ids = []

        self.current_price = random.uniform(4.5, 5.5)
        self.price_step = 0.1
        self.small_win_step = 0.01
        self.min_price = 1.0
        self.max_price = 6.0

        self.recharging_reservoirs = set()
        self.total_power_sold = 0
        self.total_timesteps = 1000
        self.recent_production = []
        self.max_timestep_seen = 0

    def got_initial_state(self):
        self.reservoir_ids = list(self.initial_state["reservoirs"].keys())

    def get_month(self):
        return (self.current_state["timestep"] % 365) // 30 + 1

    def is_high_demand_season(self):
        return 1 <= self.get_month() <= 7

    def seasonal_thresholds(self):
        month = self.get_month()
        if month <= 6:
            return (0.4, 0.7)
        progress = (month - 6) / 6  # July = 0.0, Dec = 1.0
        low = 0.4 - 0.2 * progress
        high = 0.7 - 0.2 * progress
        return (low, high)

    def other_players_water_low(self):
        others = self.current_state.get("other_players", [])
        all_levels = []
        for p in others:
            for r in p.get("reservoirs", {}).values():
                cap = r.get("capacity", 1)
                amt = r.get("water_amount", 0)
                if cap > 0:
                    all_levels.append(amt / cap)
        avg = sum(all_levels) / len(all_levels) if all_levels else 1
        return avg < 0.3

    def select_reservoirs(self):
        selected = []
        others_dry = self.other_players_water_low()
        low_thresh, high_thresh = self.seasonal_thresholds()

        for rid in self.reservoir_ids:
            res = self.current_state["reservoirs"][rid]
            w = res["water_amount"]
            cap = res["capacity"]
            pct = w / cap if cap > 0 else 0
            rivers = res.get("out_rivers", [])

            if pct < low_thresh:
                if others_dry and pct > (low_thresh - 0.1):
                    print(f"⚡ Override: releasing from {rid} at {pct:.0%} (others dry)")
                else:
                    self.recharging_reservoirs.add(rid)
            elif pct >= high_thresh:
                self.recharging_reservoirs.discard(rid)

            if rid in self.recharging_reservoirs:
                continue

            safe = True
            for r_id in rivers:
                river = self.current_state["rivers"].get(r_id)
                if river and river["current_flow"] >= river["max_flow"] * 0.95:
                    safe = False
                    break

            if w > 5 and safe:
                selected.append(rid)

        return selected

    def get_production_plan_and_power_price(self):
        ts = self.current_state["timestep"]
        print(ts)
        remaining = self.total_timesteps - ts
        demand = self.current_state.get("marked_demand", 0)
        sold = self.current_state.get("production_results", {}).get("amount", 0)
        self.total_power_sold += sold

        if sold == 0:
            self.current_price -= random.uniform(0, self.price_step)
        else:
            self.current_price += self.small_win_step

        if self.is_high_demand_season():
            self.current_price += 0.03
        if self.other_players_water_low():
            self.current_price += 0.05
        else:
            self.current_price -= 0.03

        self.current_price = max(self.min_price, min(self.current_price, self.max_price))

        if remaining <= 20:
            print(f"🚨 Endgame: {remaining} rounds left. Dumping water!")
            self.recharging_reservoirs.clear()

            dumpable = []
            for rid in self.reservoir_ids:
                res = self.current_state["reservoirs"][rid]
                if res["water_amount"] > 5:
                    safe = True
                    for r_id in res.get("out_rivers", []):
                        river = self.current_state["rivers"].get(r_id)
                        if river and river["current_flow"] >= river["max_flow"] * 0.95:
                            safe = False
                            break
                    if safe:
                        dumpable.append(rid)

            return {
                "reservoir_ids": dumpable,
                "power_price": min(self.current_price, 4.99)
            }

        selected = self.select_reservoirs()

        # Dynamic pricing band update
        was_active = bool(selected)
        self.recent_production.append(was_active)
        if len(self.recent_production) > 50:
            self.recent_production.pop(0)

        prod_rate = sum(self.recent_production) / len(self.recent_production)

        if prod_rate > 0.7:
            self.min_price += 0.01
            self.max_price += 0.02
        elif prod_rate < 0.3:
            self.min_price -= 0.02
            self.max_price -= 0.01

        self.min_price = max(0.5, min(self.min_price, 5.0))
        self.max_price = max(self.min_price + 0.5, min(self.max_price, 6.5))

        if self.current_price >= 5 and self.other_players_water_low() and demand > 0:
            self.current_price = 4.99
            print("🔽 Undercutting fallback buyer bot at 5.00")

        # Logging
        print(f"\n🕒 Timestep {ts} | 💡 Price: {self.current_price:.2f} | ⚡ Sold: {sold:.2f} | 📈 Demand: {demand}")
        for rid in self.reservoir_ids:
            res = self.current_state["reservoirs"][rid]
            w = res["water_amount"]
            m = res["capacity"]
            pct = (w / m * 100) if m else 0
            tag = "RECHARGING" if rid in self.recharging_reservoirs else "✅"
            print(f"  🏞️ {rid}: {w:,.0f}/{m:,.0f} L ({pct:.0f}%) {tag}")

        return {
            "reservoir_ids": selected,
            "power_price": round(self.current_price, 2)
        }

    def game_over(self):
        print("\n🏁 Game Over – Strategy Complete.")
        print(f"💰 Final cash: {self.current_state.get('cash', 'N/A')}")
        print(f"⚡ Total power sold: {self.total_power_sold:.2f}")



 
if __name__ == "__main__":
 
    no_produce_strategy = SmartHydroStrategy()
 
    uri = "ws://localhost:8000/ws"    
    player_name = "larry_test"
    game_id = "game1"
 
    client = Client(no_produce_strategy, uri, player_name, game_id)
    client.play()  