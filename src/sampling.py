"""-----------------------------------------------------------------------------
@Name: Flexible Bayesian Optimization (FlexiBO): An active learning for optimiz-
ing  multiple objectives of different cost
@Version: 0.1
@Author: Shahriar Iqbal
--------------------------------------------------------------------------------
"""
from __future__ import division
from src.utils import Utils
import numpy as np

class Sampling(object):
    """This class is used to determine next sample and objective
    """
    def __init__(self, o1_ind, o2_ind,
                o1_cost, o2_cost):
         print ("[STATUS]: Initializing Sample Class") 
         self.O1_IND=o1_ind
         self.O2_IND=o2_ind
         self.NUM_OBJ=2
         self.O1_COST=o1_cost
         self.O2_COST=o2_cost    
         self.utils=Utils(o1_ind, o2_ind)
         
    def determine_next_sample(self,
                             pess_pareto,
                             opt_pareto,
                             pess_indices_map,
                             opt_indices_map,
                             pess_pareto_volume,
                             opt_pareto_volume,
                             REGION,
                             E):
        """@DETERMINE_NEXT_SAMPLE
        ------------------------------------------------------------------------
        This function is used to determine next sample
        ------------------------------------------------------------------------
        """
        if pess_indices_map==opt_indices_map:
            indices_map=pess_indices_map
        pess_ind=[indices_map[i] for i in range(0,len(pess_pareto))]
        opt_ind=[indices_map[i] for i in range(0,len(opt_pareto))]
        
        pess_status=[[{"pess":True,"opt":True}] if i in opt_ind else [{"pess":True,"opt":False}] for i in pess_ind]
        opt_status=[[{"pess":True,"opt":True}] if i in pess_ind else [{"pess":False,"opt":True}] for i in opt_ind]
        
        #-----------------------------------------------------------------------
        # compute dv/c for each point in pessimistic pareto front
        #-----------------------------------------------------------------------
        dv_per_cost_pess=[{"o1":0,"o2":0} for i in pess_ind]
        for i in range(0,len(pess_pareto)):                   
             for j in range(0,self.NUM_OBJ):
                 # Update pessimistic pareto front shring pess to avg  
                 if pess_status[i][0]["pess"] is True:    
                     cur_pess=pess_pareto[:]
                     # replace pess with avg value across O1
                     cur_pess[i][j]=REGION[pess_ind[i]]["avg"][j]
                     cur_pess_pareto=self.utils.construct_pessimistic_pareto_front(pess_ind,
                                                                              cur_pess,
                                                                              "UPDATE")
                     cur_pess_volume=self.utils.compute_pareto_volume(cur_pess_pareto)
                 
                 # Update optimistic pareto front shring pess to avg
                 if pess_status[i][0]["opt"] is True: 
                     cur_opt=opt_pareto[:]
                     opt_i=opt_ind.index(pess_ind[i])
                     # replace opt with avg value across O1
                     cur_opt[opt_i][j]=REGION[opt_ind[i]]["avg"][j]
                     cur_opt_pareto=self.utils.construct_optimistic_pareto_front(opt_ind,
                                                                                 cur_opt,
                                                                                 "UPDATE")
                     cur_opt_volume=self.utils.compute_pareto_volume(cur_opt_pareto)
                 
                 # Shrinking of pessimistic pareto points do not change optimistic
                 # pareto front
                 if pess_status[i][0]["opt"] is False:
                     cur_opt_volume=opt_pareto_volume
                 
                 dv=(opt_pareto_volume-pess_pareto_volume)-(cur_opt_volume-cur_pess_volume)
                 if j==self.O1_IND:
                     dv_per_cost_pess[i]["o1"]=dv/self.O1_COST
                 if j==self.O2_IND:
                     dv_per_cost_pess[i]["o2"]=dv/self.O2_COST
        #-----------------------------------------------------------------------
        # compute dv/c for each point in optimistic pareto front
        #-----------------------------------------------------------------------
        dv_per_cost_opt=[{"o1":0,"o2":0} for i in opt_ind]
        for i in range(0,len(opt_pareto)):                   
             for j in range(0,self.NUM_OBJ):
                 # Update optimistic pareto front shring opt to avg. Similar points
                 # both in pess and opt pareto fronts are already covered in
                 # pessimistic pareto front update computation         
                 if (opt_status[i][0]["opt"] is True and 
                     opt_status[i][0]["opt"] is False):
                     
                     cur_opt=opt_pareto[:]
                     # replace pess with avg value across O1
                     cur_opt[i][j]=REGION[opt_ind[i]]["avg"][j]
                     cur_opt_pareto=self.utils.construct_optimistic_pareto_front(opt_ind,
                                                                              cur_opt,
                                                                              "UPDATE")
                     cur_opt_volume=self.utils.compute_pareto_volume(cur_opt_pareto)
                     # Shrinking of optimistic pareto points do not change pessimistic
                     # pareto front
                     cur_pess_volume=pess_pareto_volume
                 
                 # Compute dv per cost for each objective
                 dv=(opt_pareto_volume-pess_pareto_volume)-(cur_opt_volume-cur_pess_volume)
                 if j==self.O1_IND:
                     dv_per_cost_opt[i]["o1"]=dv/self.O1_COST
                 if j==self.O2_IND:
                     dv_per_cost_opt[i]["o2"]=dv/self.O2_COST         
        #-----------------------------------------------------------------------
        # Compute max dv per cost to determine the next sample and objective
        #-----------------------------------------------------------------------
        max_dv_per_cost=0
        objective="o1"
        
        # Compute max dv per cost from pessimistic pareto points      
        for i in range(0,len(dv_per_cost_pess)):
            if abs(dv_per_cost_pess[i]["o1"])>=max_dv_per_cost:
                max_dv_per_cost_ind=i
                max_dv_per_cost=abs(dv_per_cost_pess[i]["o1"])
                objective="o1"
            if abs(dv_per_cost_pess[i]["o2"])>=max_dv_per_cost:
                max_dv_per_cost_ind=i
                max_dv_per_cost=abs(dv_per_cost_pess[i]["o2"])
                objective="o2"
        cur_dv_per_cost_ind=indices_map[max_dv_per_cost_ind]
        
        # Compute max dv per cost from optimistic pareto points
        for i in range(0,len(dv_per_cost_opt)):
            if abs(dv_per_cost_opt[i]["o1"])>=max_dv_per_cost:
                max_dv_per_cost_ind=i
                max_dv_per_cost=abs(dv_per_cost_pess[i]["o1"])
                objective="o1"
            if abs(dv_per_cost_opt[i]["o2"])>=max_dv_per_cost:
                max_dv_per_cost_ind=i
                max_dv_per_cost=abs(dv_per_cost_pess[i]["o2"])
                objective="o2"
        
        # Compute next sample
        cur_dv_per_cost_ind=indices_map[max_dv_per_cost_ind]
        
        next_sample=E[cur_dv_per_cost_ind]
        return (cur_dv_per_cost_ind,
                next_sample, 
                objective)
        
