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
        self.current_price = random.uniform(4, 5)
        self.price_step = 0.1
        self.small_win_step = 0.01
        self.min_price = 1
        self.max_price = 5   

        # Internal state tracking
        self.prev_demands = []
        self.prev_sales = []
        self.total_power_sold = 0
        self.recharging_reservoirs = set()

    def got_initial_state(self):
        self.reservoir_ids = list(self.initial_state["reservoirs"].keys())
        self.total_timesteps = self.initial_state.get("timesteps", 365)

    def get_month(self):
        timestep = self.current_state["timestep"]
        return (timestep % 365) // 30 + 1

    def is_high_demand_season(self):
        return 1 <= self.get_month() <= 7

    def other_players_water_low(self):
        other_players = self.current_state.get("other_players", [])
        fullness = []

        for p in other_players:
            for r in p.get("reservoirs", {}).values():
                max_w = r.get("capacity", 1)
                w = r.get("water_amount", 0)
                if max_w > 0:
                    fullness.append(w / max_w)

        avg = sum(fullness) / len(fullness) if fullness else 1
        return avg < 0.3

    def select_reservoirs(self):
        selected = []
        others_are_dry = self.other_players_water_low()

        for rid in self.reservoir_ids:
            res = self.current_state["reservoirs"][rid]
            w = res["water_amount"]
            max_w = res["capacity"]
            fill_pct = w / max_w if max_w > 0 else 0
            rivers = res.get("out_rivers", [])

            # Refill condition
            if fill_pct < 0.15:
                if others_are_dry and fill_pct > 0.25:
                    print(f"⚡ Override: releasing from {rid} at {fill_pct:.0%} (others dry)")
                else:
                    self.recharging_reservoirs.add(rid)
            elif fill_pct >= 0.45:
                self.recharging_reservoirs.discard(rid)

            if rid in self.recharging_reservoirs:
                continue

            safe = True
            for r_id in rivers:
                river = self.current_state["rivers"][r_id]
                if river["current_flow"] >= river["max_flow"] * 0.75:
                    safe = False
                    break

            if w > 5 and safe:
                selected.append(rid)

        return selected

    def get_production_plan_and_power_price(self):
        timestep = self.current_state["timestep"]
        demand = self.current_state.get("marked_demand", 0)
        sales_volume = self.current_state.get("production_results", {}).get("amount", 0)
        ts = self.current_state["timestep"]
        remaining = self.total_timesteps - ts
        self.total_power_sold += sales_volume
        self.prev_demands.append(demand)
        self.prev_sales.append(sales_volume)

        # Pricing dynamics
        if sales_volume == 0:
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
        selected = self.select_reservoirs()

        # Final 20 rounds: release it all
        # ✅ Rich Logging
        print(f"\n🕒 Timestep {timestep}")
        print(f"💡 Price: {self.current_price:.2f} | ⚡ Sold: {sales_volume:.2f} | 📈 Demand: {demand}")
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
 
    uri = "ws://192.168.16.69:8000/ws"    
    player_name = "Mama_Larry"
    game_id = "game1"
 
    client = Client(no_produce_strategy, uri, player_name, game_id)
    client.play()  
 