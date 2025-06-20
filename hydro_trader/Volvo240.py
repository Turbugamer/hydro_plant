from client import Strategy, Client

# times 900 pc

class OwnStrategy(Strategy):
    def __init__(self):
        super().__init__()

    #def random_walk(self, )

    def trade(self):
        """
        Returns a list of reservoirs to produce and the power price
        
        # full initial state: self.initial_state
        # full current state: self.current_state
        """

        print("timestep: {}, cash; {}. marked demand: {}".format(self.current_state["timestep"], self.current_state["cash"], self.current_state["marked_demand"]))
        
        demand = self.current_state["marked_demand"]
        if demand < 0.3 * self.current_state["total_demand"]:
            print("Demand is low, not producing.")
            return {
                "reservoir_ids": [],
                "power_price": 0
            }
        elif demand > 0.7 * self.current_state["total_demand"]:
            print("Demand is high, producing all.")
            self.reservoir_ids = list(self.initial_state["reservoirs"].keys())
            return {
                "reservoir_ids": self.reservoir_ids,
                "power_price": 10.0
            }
        else:
            print("Demand is moderate, producing selectively.")
            self.reservoir_ids = list(self.initial_state["reservoirs"].keys())
            return {
                # produce with only 2 or 3 water plants that has most water in them

                "reservoir_ids": self.reservoir_ids[:len(self.reservoir_ids)//2],  # Produce with half of the reservoirs
                "power_price": 7.5
            }
            #print("timestep: {}, cash; {}. marked demand: {}".format(self.current_state["timestep"], self.current_state["cash"], self.current_state["marked_demand"]))

        """ 
        plan = {
            "reservoir_ids": [], # the names of the reservoirs that should produce power
            "power_price": 0 # the power price
        }

        plan["reservoir_ids"].append("Vestarne") # always produce with Vestarne
        plan["reservoir_ids"] = self.reservoir_ids # produce all

        if plan["reservoir_ids"] > (0.3*

        plan["power_price"] = 5.69 # price
        return plan
        """
if __name__ == "__main__":

    no_produce_strategy = Strategy()

    uri = "ws://localhost:8000/ws"    
    player_name = "player1"
    game_id = "game1"

    client = Client(no_produce_strategy, uri, player_name, game_id)
    client.play()  
