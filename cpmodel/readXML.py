import xml.etree.ElementTree as ET
import sys

def readXMLProject(file):
    
    # Parse XML file
    tree = ET.parse(file)

    # Get root node
    root = tree.getroot()

    for parameters in root.findall("./parameters"):
        sierra = int(parameters.attrib["sawwith"])        

    cuts=[]    
    for cut in root.findall("./cuts/cut"):
        cuts.append({"length":int(cut.attrib["length"]), "quantity":int(cut.attrib["quantity"])})
    
    bars=[]
    for bar in root.findall("./stock/bar"):
        bars.append({"length":int(bar.attrib["length"])
                     , "quantity":int(bar.attrib["quantity"]) 
                     , "ltrim":int(bar.attrib["ltrim"]) 
                     , "rtrim":int(bar.attrib["rtrim"]) 
                     })        
    
    '''for cuts in root.findall("./cuts/cut"):
        cuts.append(cuts.attrib["length"])'''
    '''medidasreq = []
    for mreq in root.findall("./medidasrequeridas/medida"):
        medidasreq.append({"longitud":int(mreq.attrib["longitud"]),"cantidad":int(mreq.attrib["cantidad"])})'''
    
    #print(medidasreq[0]["longitud"])
    #print("Medidas requeridas: ",medidasreq)

    '''medidasstock = []
    for mreq in root.findall("./medidasstock/medida"):
        medidasstock.append({"longitud":int(mreq.attrib["longitud"]),"cantidad":int(mreq.attrib["cantidad"])})'''

    #print("Medidas Stock: ", medidasstock)

    #return sierra, despunteizq, despunteder, medidasreq, medidasstock
    return sierra, cuts, bars
