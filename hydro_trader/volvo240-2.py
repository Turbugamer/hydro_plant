from client import Strategy, Client
import random
from datetime import datetime
#from utilities.utils import write_file
import os
# times 900 pc
import random
from datetime import datetime


class SmartHydroStrategy:
    def __init__(self):
        self.player_id = None
        self.initial_state = None
        self.current_state = None
        self.reservoir_ids = []

        # Pricing behavior
        self.current_price = random.uniform(4, 4.999999)
        self.price_step = 0.1
        self.small_win_step = 0.01
        self.min_price = 0.5
        self.max_price = 4.9999999

        self.recharging_reservoirs = set()
        self.total_power_sold = 0
        self.total_timesteps = 1000  # Default, gets overwritten later

    def got_initial_state(self):
        self.reservoir_ids = list(self.initial_state["reservoirs"].keys())

    def get_month(self):
        return (self.current_state["timestep"] % 365) // 30 + 1

    def is_high_demand_season(self):
        return 1 <= self.get_month() <= 7

    def other_players_water_low(self):
        other_players = self.current_state.get("other_players", [])
        fullness = []
        for p in other_players:
            for r in p.get("reservoirs", {}).values():
                cap = r.get("capacity", 1)
                amt = r.get("water_amount", 0)
                if cap > 0:
                    fullness.append(amt / cap)
        avg = sum(fullness) / len(fullness) if fullness else 1
        return avg < 0.45

    def select_reservoirs(self):
        selected = []
        others_dry = self.other_players_water_low()

        for rid in self.reservoir_ids:
            res = self.current_state["reservoirs"][rid]
            water_amount= res["water_amount"]
            max_w = res["capacity"]
            pct =water_amount/ max_w if max_w > 0 else 0
            rivers = res.get("out_rivers", [])

            if pct < 0.4:
                if others_dry and pct > 0.2:
                    print(f"⚡ Override: releasing from {rid} at {pct:.0%} (others dry)")
                else:
                    self.recharging_reservoirs.add(rid)
            elif pct >= 0.75:
                self.recharging_reservoirs.discard(rid)

            if rid in self.recharging_reservoirs:
                continue

            # River safety check
            safe = True
            for r_id in rivers:
                river = self.current_state["rivers"][r_id]
                if river["current_flow"] >= river["max_flow"] * 0.975:
                    safe = False
                    break

            if water_amount> 5 and safe:
                selected.append(rid)

        return selected

    def get_production_plan_and_power_price(self):
        ts = self.current_state["timestep"]
        print(ts)
        remaining = self.total_timesteps - ts
        demand = self.current_state.get("marked_demand", 0)
        sold = self.current_state.get("production_results", {}).get("amount", 0)
        self.total_power_sold += sold

        # Price tweaks
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

        # Undercut buyer bot if needed
        if self.current_price >= 5 and self.other_players_water_low() and demand > 0:
            self.current_price = 4.99
            print("🔽 Undercutting buyer bot at price 5.00")

        self.current_price = max(self.min_price, min(self.current_price, self.max_price))

        # Final 20 rounds: release it all
        if remaining <= 20:
            print(f"🚨 Endgame: {remaining} rounds left. Dumping water!")
            return {
                "reservoir_ids": self.reservoir_ids,
                "power_price": min(self.current_price, 4.99)
            }

        selected = self.select_reservoirs()

        print(f"\n🕒 Timestep {ts} | Price: {self.current_price:.2f} | Sold: {sold:.2f} | Demand: {demand}")
        for rid in self.reservoir_ids:
            res = self.current_state["reservoirs"][rid]
            water_amount = res["water_amount"]
            m = res["capacity"]
            pct = (water_amount / m * 100) if m else 0
            tag = "RECHARGING" if rid in self.recharging_reservoirs else "✅"
            print(f"  🏞️ {rid}: {water_amount:,.0f}/{m:,.0f} L ({pct:.0f}%) {tag}")

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
 