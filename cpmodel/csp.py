from readXML import readXMLProject
from csp_optimizer import optimize

sawwidth, cuts, bars = readXMLProject("cuts.xml")
status, bl, waste = optimize(sawwidth, cuts, bars)

for i in range(len(bl)):
    print(bl[i])
print(f"desperdicio: {waste}")