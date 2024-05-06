# Semi-parametric cluster-weighted multilevel models for two levels clustering
Master thesis on the development of a novel multi-level cluster- weighted model able to find two levels of clustering for hierarchical data on both unit and group levels

ALGORITHM:
- algo_full.py

SIMULATION STUDY:
One case of simulation study in which I check the validity of the propose model analysing.
- Parameter distribution: analysis of the estimated parameters compared with the true ones
- Models comparison: comparison of the accuracy  of the proposed model with that of other models commonly found in the literature, such as GLM and GLMER
- Wrong Number Profiles: analysis of the behaviour of the model using as input an wrong number of profiles providing also a model selection technique using AIC and BIC indexes

CASE STUDY:
Practical application of the proposed model to data extracted from OECD-PISA in 2018 with the purpose of analyse the math level of European students. The goal is to model the probability of a student of being under the minimum proficiency level required in math, by investigating the effect of the student background, of the heterogeneous psychological profiles and of the country-specific educational system.
