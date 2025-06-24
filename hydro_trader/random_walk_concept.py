from client import Strategy, Client
import random
from datetime import datetime
#from utilities.utils import write_file
import os
# times 900 pc
 
 
class SmartHydroStrategy:
    def __init__(self):
        self.player_id = None
        self.initial_state = None
        self.current_state = None
        self.reservoir_ids = []
 
        # Pricing strategy
        self.current_price = random.uniform(4.5, 5.5)
        self.price_step = 0.1
        self.min_price = 1
        self.max_price = 5
 
        # History tracking
        self.prev_demands = []
        self.prev_sales = []
 
    def got_initial_state(self):
        self.reservoir_ids = list(self.initial_state["reservoirs"].keys())
 
    def get_month(self):
        """Returns the current in-game month (1–12) based on timestep."""
        timestep = self.current_state["timestep"]
        return (timestep % 365) // 30 + 1  # crude month estimate
 
    def is_high_demand_season(self):
        month = self.get_month()
        return 1 <= month <= 7  # Jan–July
 
    def select_reservoirs(self):
        """Select reservoirs that can safely produce without overfilling downstream rivers."""
        selected = []
        for rid in self.reservoir_ids:
            res = self.current_state["reservoirs"][rid]
            stored = res["water_amount"]
            connections = res.get("connected_rivers", [])
 
            # Check if downstream rivers can handle more water
            safe_to_release = True
            for river_id in connections:
                river = self.current_state["rivers"][river_id]
                if river["current_volume"] >= river["max_volume"] * 0.95:
                    safe_to_release = False
                    break
 
            if stored > 5 and safe_to_release:
                selected.append(rid)
 
        return selected
 
    def get_production_plan_and_power_price(self):
        demand = self.current_state.get("marked_demand", 0)
        sales_volume = self.current_state.get("sales_volume", 0)
 
        # Track history
        self.prev_demands.append(demand)
        self.prev_sales.append(sales_volume)
 
        # Adjust price based on sales and season
        if sales_volume == 0:
            self.current_price -= random.uniform(0, self.price_step)  # Undercut more
        elif self.is_high_demand_season():
            self.current_price += random.uniform(0, self.price_step / 2)  # Slight bump
        else:
            self.current_price += random.uniform(-self.price_step, self.price_step)  # Explore
 
        # Clamp price
        self.current_price = max(self.min_price, min(self.current_price, self.max_price))
 
        # Select safe reservoirs
        active_reservoirs = self.select_reservoirs()
        #write_file(self, os.path.basename(__file__).removesuffix('.py'))
 
        return {
            "reservoir_ids": active_reservoirs,
            "power_price": round(self.current_price, 2)
        }
 

    def game_over(self):
        print("Game over. Strategy finished.")
        print(f"💰 Final cash: {self.current_state.get('cash', 'N/A')}")

 
if __name__ == "__main__":
 
    no_produce_strategy = SmartHydroStrategy()
 
    uri = "ws://localhost:8000/ws"    #Choose Other user's IP to play in same environment
    player_name = "larry_test"
    game_id = "game1"
 
    client = Client(no_produce_strategy, uri, player_name, game_id)
    client.play()  
 