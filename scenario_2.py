#SCENARIO DEFINING CONSTRAINT IS IN LINE 137

#Importing Libraries
import numpy as np
import matplotlib.pyplot as plt
from docplex.mp.model import Model
#from docplex.mp.solution import SolveSolution, SolutionPool
from math import sqrt
    
x = np.loadtxt('optdata.txt', skiprows = 1, usecols=0)
y = np.loadtxt('optdata.txt', skiprows=1, usecols=1)
pop = np.loadtxt('optdata.txt', skiprows=1, usecols = 2)
farm_num = np.loadtxt('optdata.txt', skiprows=1, usecols = 3)
land_area = np.loadtxt('optdata.txt', skiprows=1, usecols = 4)
farm_density = np.loadtxt('optdata.txt', skiprows=1, usecols = 5)
pop_density = np.loadtxt('optdata.txt', skiprows=1, usecols = 6)

ghg_data = np.loadtxt('fake_env_data.txt', skiprows=1, usecols=0)
biodiv_data = np.loadtxt('fake_env_data.txt', skiprows=1, usecols=1)
soil_data = np.loadtxt('fake_env_data.txt', skiprows=1, usecols=2)

road_data = np.loadtxt('fake_road_rail.txt', skiprows=1, usecols=0)
rail_data = np.loadtxt('fake_road_rail.txt', skiprows=1, usecols=1)

biomass_data_quantitydemand = np.loadtxt('fake_supply_demand.txt', skiprows=1, usecols=0)
biomass_data_quantitysupply = np.loadtxt('fake_supply_demand.txt', skiprows=1, usecols=1)



#Create the model
model = Model()

#Biorefinery object class for creating and storing the information for them, no methods defined as of yet
class Biorefinery(object):
    
        def __init__(self,  x_coord, y_coord, demand):         
            self.x_coord = x_coord
            self.y_coord = y_coord
            self.demand = demand
            

        
class SubDivision(object):
    
    def __init__(self, x_coord, y_coord, farmdens, popdens, ghg, biodiv, soil, ecocost, envcost, road, rail,supply):       
            self.x_coord = x_coord
            self.y_coord = y_coord
            self.farmdens = farmdens
            self.popdens = popdens
            self.ghg = ghg
            self.biodiv = biodiv
            self.soil = soil
            self.ecocost = ecocost
            self.envcost = envcost
            self.road = road
            self.rail = rail
            self.supply = supply
          
            

#Creating a new distance function
def Distance(Pone, Ptwo):
    distance = sqrt( (Pone[0]-Ptwo[0])**2 + (Pone[1]-Ptwo[1])**2)
    return distance        
            


class hub(object):
    
    def __init__(self, x_coord, y_coord):
        self.x_coord = x_coord
        self.y_coord = y_coord

        


#list of biorefineries
#biorefineries = [B1,B2,B3,B4]
nb_biorefineries = 4
print('We would like to open', nb_biorefineries, 'biorefineries.')


#Potential fix for our distance calculation problem




subdivs = []
refinies = []


for i in range(0,37):
     subdivs.append(SubDivision(x[i], y[i], farm_density[i], pop_density[i], ghg_data[i], biodiv_data[i], soil_data[i], 0,0,road_data[i], rail_data[i], biomass_data_quantitysupply[i]))


for i in range(0,37):
     refinies.append(Biorefinery(x[i], y[i], biomass_data_quantitydemand[i]))



## DECISION VARS
# Binary vars indicating which biorefinery locations will be actually selected
biorefinery_vars = model.binary_var_dict(refinies, name = "is_refinery")

# Binary vars representing the "assigned" farms for each biorefineries
s_b_link = model.binary_var_matrix(refinies, subdivs, "link")


## CONSTRAINTS
#Constraint on the distance between farms and biorefineries
#If the distance is greater than BIGDIST the link var equals zero and that means the farm is not selected
MAXDIST = 100
MAXPOP = 150
MAXGHG = 38
MAXBIODIV = 40
MAXSOIL = 40


for b in refinies:
    for f in subdivs:
        if Distance((b.x_coord,b.y_coord), (f.x_coord,f.y_coord)) >= MAXDIST:
            model.add_constraint(s_b_link[b, f] == 0)
        
        if f.popdens > MAXPOP:
              model.add_constraint(s_b_link[b, f] == 0)

        if f.ghg > MAXGHG:
             model.add_constraint(s_b_link[b, f] == 0)

        if f.biodiv > MAXBIODIV:
             model.add_constraint(s_b_link[b, f] == 0)

        if f.soil > MAXSOIL:
             model.add_constraint(s_b_link[b, f] == 0)

        if b.demand > f.supply:
             model.add_constraint(s_b_link[b,f]==0) #SCENARIO DEFINING CONSTRAINT

          


for s in subdivs:
     if s.road > s.rail:
          s.ecocost = 2.714 #In CAD
          s.envcost = 50 * 19.958 * (81.14/1000000) #see notes for explanation of this calculation (has many conversion factors)

     if s.road < s.rail:
          s.ecocost = 1.183 #In CAD
          s.envcost = 50 * 19.958 * (13.05/1000000) #see notes for explanation of this calculation all in canadian dollars and tonnes not tons
     


#linked one to one
model.add_constraints(s_b_link[b, s] <= biorefinery_vars[b] for b in refinies for s in subdivs)

#linked to open spots
model.add_constraints(model.sum(s_b_link[c_loc, b] for c_loc in refinies) == 1 for b in subdivs)
      
   
#Constraint on total nb of open biorefineries
model.add_constraint_(model.sum(biorefinery_vars[b] for b in refinies) == nb_biorefineries)


## Objective Function
total_cost = model.sum(f.ecocost * s_b_link[b, f] * Distance((b.x_coord,b.y_coord), (f.x_coord,f.y_coord)) for b in refinies for f in subdivs) + model.sum(f.envcost * s_b_link[b, f] * Distance((b.x_coord,b.y_coord), (f.x_coord,f.y_coord))  for b in refinies for f in subdivs)
model.minimize(total_cost)

##SOLVING MODEL
model.solve(log_output=True)  #printing information about the iterations
print(model.solve_details)

##PRINTING SOLUTION VALUES
print('Total Cost', model.objective_value)



for b_loc in refinies:
    if biorefinery_vars[b_loc].solution_value ==1:
        print('location changed', "location: ", b_loc.x_coord,b_loc.y_coord)


