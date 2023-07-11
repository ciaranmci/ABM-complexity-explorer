#Import Dependencies


import mesa
import numpy as np
import math
import matplotlib.pyplot as plt


#Resource Classes

class Sugar(mesa.Agent):
  """
  Sugar: 
  - contains an amount of sugar
  - grows 1 amount of sugar at each turn 
  """

  def __init__(self, unique_id, model, pos, max_sugar): 
    super().__init__(unique_id, model)
    self.pos = pos
    self.amount = max_sugar
    self.max_sugar = max_sugar
    
  def step(self):
    '''
    Sugar Growth function, adds one unit of sugar each step until
    max amount
    '''
    self.amount = min([self.max_sugar, self.amount + 1])

    

class Spice(mesa.Agent):
  """
  Spice: 
  - contains an amount of spice
  - grows 1 amount of spice at each turn
  """

  def __init__(self, unique_id, model, pos, max_spice):
    super().__init__(unique_id, model)
    self.pos = pos
    self.amount = max_spice
    self.max_spice = max_spice
  
  def step(self):
    '''
    Sugar Growth function, adds one unit of sugar each step until
    max amount
    '''
    self.amount = min([self.max_spice, self.amount + 1])

#Trader Agent

class Trader(mesa.Agent): 
  """
  Trader: 
  - has a metabolism of sugar and spice
  - harvest and trade sugar and spice to survive
  """
  
  def __init__(self, unique_id, model, pos, moore = False, sugar = 0,
               spice = 0, metabolism_sugar = 0, metabolism_spice = 0,
               vision = 0):
    super().__init__(unique_id, model)
    self.pos = pos
    self.moore = moore
    self.sugar = sugar
    self.spice = spice
    self.metabolism_sugar = metabolism_sugar
    self.metabolism_spice = metabolism_spice
    self.vision = vision
  
    
  def get_sugar_amount(self, pos):
      """
      Used in self.move() as part of calculate_welfare()

      """
      
      sugar_patch = self.get_sugar(pos)
      if sugar_patch:
          return sugar_patch.amount
      return 0
    
    
  def is_occupied_by_other(self, pos):
      '''
      helper function part 1 of self.move()
      '''
      
      if pos == self.pos:
          # agent's position is considered unoccupied as agent can stay there.
          return False
      # get contents each cell in neighbourhood
      this_cell = self.model.grid.get_cell_list_contents(pos)
      for a in this_cell:
          # see if occupied by another agent.
          if isinstance(a, Trader):
              return True
      return False
  
  def calculate_welfare(self, sugar, spice):
      """
      Helper functions part 2 self.move()
      """
      
      # Calculate total resources that the agent has.
      resource_total = self.metabolism_sugar + self.metabolism_spice
      # Cobb-Douglas functional form.
      return sugar**(self.metabolism_sugar / resource_total) * spice**(
          self.metabolism_spice / resource_total)
      
  def move(self):
      '''
      Function for trader agent to identify optimal move for each step in 4 parts
      1 - identify all possible moves.
      2 - determine which move mximises welfare
      3 - find closest best option
      4 - move
      '''
            
      # 1 - identify all possible moves.
      neighbours = [i
                    for i in self.model.grid.get_neighborhood(
                            self.pos, self.moore, True, self.vision
                            ) if not self.is_occupied_by_other(i)]
      
      # 2 - Determine which move maximises welfare.
      welfares = [
          self.calculate_welfare(self.sugar + self.get_sugar_amount(pos),
                                 self.spice + self.get_spice_amount(pos))
          for pos in neighbours
          ]
      print(welfares)

#Model Class

class SugarscapeG1mt(mesa.Model):
  """
  Manager class to run Sugarscape with Traders
  """
  
  
  def __init__(self, width = 50, height = 50, initial_population = 200,
               endowment_min = 25, endowment_max = 50, metabolism_min = 1,
               metabolism_max = 5, vision_min = 1, vision_max = 5):
    
    # Initiate width and heigh of sugarscape.
    self.width = width
    self.height = height
    
    # Initiate population attributes.
    self.initial_population = initial_population
    self.endowment_min = endowment_min
    self.endowment_max = endowment_max
    self.metabolism_min = metabolism_min
    self.metabolism_max = metabolism_max
    self.vision_min = vision_min
    self.vision_max = vision_max
    
    # Initiate scheduler
    self.schedule = mesa.time.RandomActivationByType(self)
    
    # Initiate mesa grid class.
    self.grid = mesa.space.MultiGrid(self.width, self.height, torus = False)
        
    # Read in landscape file from supplmentary material .
    sugar_distribution = np.genfromtxt("sugar-map.txt")
    spice_distribution = np.flip(sugar_distribution, 1)
    
    plt.imshow(spice_distribution, origin="lower")
        
    agent_id = 0
    for _,x,y in self.grid.coord_iter():
      max_sugar = sugar_distribution[x,y]
      if max_sugar > 0: 
        sugar = Sugar(agent_id, self, (x,y), max_sugar)
        self.schedule.add(sugar)
        self.grid.place_agent(sugar, (x,y))
        agent_id += 1
    
      max_spice = spice_distribution[x,y]
      if max_spice > 0:
        spice = Spice(agent_id, self, (x,y), max_spice)
        self.schedule.add(spice)
        self.grid.place_agent(spice, (x,y))
        agent_id += 1
    
    for i in range(self.initial_population):
        # Get agent position.
        x = self.random.randrange(self.width)
        y = self.random.randrange(self.height)
        
        # Give agents initial endowment
        sugar = int(self.random.uniform(self.endowment_min, self.endowment_max))
        spice = int(self.random.uniform(self.endowment_min, self.endowment_max))
        
        # Give agents initial metabolism.
        metabolism_sugar = int(self.random.uniform(self.metabolism_min, self.metabolism_max))
        metabolism_spice = int(self.random.uniform(self.metabolism_min, self.metabolism_max))
        
        # Give agents vision
        vision = int(self.random.uniform(self.vision_min, self.vision_max))
        
        # Create trader object
        trader = Trader(agent_id,
                        self,
                        (x,y),
                        moore = False,
                        sugar = sugar,
                        spice = spice,
                        metabolism_sugar = metabolism_sugar,
                        metabolism_spice = metabolism_spice,
                        vision = vision
                        )
        
        # Place agent.
        self.grid.place_agent(trader, (x,y))
        self.schedule.add(trader)
        agent_id += 1
        
  def step(self):
    '''
    Unique step function that combines stage activation
    of sugar and spice, and then randomly activates traders.
    '''
    
    for sugar in self.schedule.agents_by_type[Sugar].values():
        sugar.step()
    
    for spice in self.schedule.agents_by_type[Spice].values():
        spice.step()
    
    # Step trader agents
    '''
    To accout for agent death and removal, we need to separate data
    structure to iterate.
    '''
    trader_shuffle = list(self.schedule.agents_by_type[Trader].values())
    self.random.shuffle(trader_shuffle)
    
    for agent in trader_shuffle:
        agent.move()
    
    
    self.schedule.steps += 1 # important for data collector to track number of
                             # steps
  def run_model(self, step_count = 1000):
      
      for i in range(step_count):
          print(i)
          self.step()
# Run Sugarscape.

model = SugarscapeG1mt()
model.run_model(step_count = 5)
for i in range(5):
    model.step()

 

