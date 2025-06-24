from client import Strategy, Client
import random
from datetime import datetime
#from utilities.utils import write_file
import os
# times 900 pc
import random
from datetime import datetime


import random

import random

import random

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
        self.min_price = 3.75
        self.max_price = 4.9999

        self.recharging_reservoirs = set()
        self.total_power_sold = 0
        self.total_timesteps = 200
        self.recent_production = []
        self.max_timestep_seen = 0
        self.last_release_timestep = {}  # Cooldown tracking

    def got_initial_state(self):
        self.reservoir_ids = list(self.initial_state["reservoirs"].keys())
        self.total_timesteps = self.initial_state.get("timesteps", 365)

    def get_month(self):
        return (self.current_state["timestep"] % 365) // 30 + 1

    def is_high_demand_season(self):
        return 1 <= self.get_month() <= 7

    def seasonal_thresholds(self):
        month = self.get_month()
        if month <= 6:
            return (0.4, 0.6)
        progress = (month - 6) / 6
        low = 0.4 - 0.2 * progress
        high = 0.6 - 0.2 * progress
        return (low, high)

    def other_players_water_low(self):
        others = self.current_state.get("other_players", [])
        levels = [
            r["water_amount"] / r["capacity"]
            for p in others
            for r in p.get("reservoirs", {}).values()
            if r.get("capacity", 0) > 0
        ]
        return sum(levels) / len(levels) < 0.4 if levels else False

    def select_reservoirs(self):
        selected = []
        others_dry = self.other_players_water_low()
        low_thresh, high_thresh = self.seasonal_thresholds()
        timestep = self.current_state["timestep"]

        for rid in self.reservoir_ids:
            res = self.current_state["reservoirs"][rid]
            w = res["water_amount"]
            cap = res["capacity"]
            pct = w / cap if cap > 0 else 0
            rivers = res.get("out_rivers", [])
            max_flow = res.get("max_generator_flow", 0)
            planned_flow = max_flow * 0.7  # Safer partial flow

            # Recharging logic
            if pct < low_thresh:
                if others_dry and pct > (low_thresh - 0.1):
                    pass  # Opportunistic override
                else:
                    self.recharging_reservoirs.add(rid)
            elif pct >= high_thresh:
                self.recharging_reservoirs.discard(rid)

            # Cooldown check
            last_used = self.last_release_timestep.get(rid, -999)
            if timestep - last_used < 5:
                continue

            if rid in self.recharging_reservoirs:
                continue

            # River safety check
            safe = True
            for r_id in rivers:
                river = self.current_state["rivers"].get(r_id)
                if river:
                    projected = river["current_flow"] + planned_flow
                    if projected > river["max_flow"] * 0.9:
                        safe = False
                        break

            if w > 5 and safe:
                selected.append(rid)
                self.last_release_timestep[rid] = timestep  # Update cooldown

        return selected

    def get_production_plan_and_power_price(self):
        ts = self.current_state["timestep"]
        self.max_timestep_seen = max(self.max_timestep_seen, ts)
        remaining = self.total_timesteps - ts
        demand = self.current_state.get("marked_demand", 0)
        sold = self.current_state.get("production_results", {}).get("amount", 0)
        self.total_power_sold += sold

        # Price drift
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

        # Clamp pricing
        self.current_price = max(self.min_price, min(self.current_price, self.max_price))

        # Endgame release
        if remaining <= 20:
            self.recharging_reservoirs.clear()
            dumpable = []
            for rid in self.reservoir_ids:
                res = self.current_state["reservoirs"][rid]
                flow = res.get("max_generator_flow", 0) * 0.5
                if res["water_amount"] > 5:
                    safe = True
                    for r_id in res.get("out_rivers", []):
                        river = self.current_state["rivers"].get(r_id)
                        if river and river["current_flow"] + flow > river["max_flow"] * 0.65:
                            safe = False
                            break
                    if safe:
                        dumpable.append(rid)
                        self.last_release_timestep[rid] = ts

            return {
                "reservoir_ids": dumpable,
                "power_price": min(self.current_price, 4.99)
            }

        # Standard selection
        selected = self.select_reservoirs()

        # Adjust adaptive price band
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

        # Undercut buyer bot
        if self.current_price >= 5 and self.other_players_water_low() and demand > 0:
            self.current_price = 4.99

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
 
    uri = "ws://192.168.16.69:8000/ws"    
    player_name = "Baba_Larry"
    game_id = "game1"
 
    client = Client(no_produce_strategy, uri, player_name, game_id)
    client.play()  